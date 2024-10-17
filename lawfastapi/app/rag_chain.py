import aiosqlite.context
from retrieval_chain.pdf import PDFRetrievalChain
from retrieval_chain.utils import format_docs
from schema.graph_state import GraphState
from langchain_upstage import UpstageGroundednessCheck
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, START, StateGraph
from config.static_variables import StaticVariables
import aiosqlite
import asyncio

# ragas 평가
from langchain_teddynote.community.pinecone import PineconeKiwiHybridRetriever
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_recall,
    context_precision
)
import pandas as pd
from tqdm.auto import tqdm
from datasets import Dataset

# 검색결과 보기 좋게 출력하기 위한 함수
def pretty_print(docs):
    for i, doc in enumerate(docs):
        if "score" in doc.metadata:
            print(f"[{i + 1}] {doc.page_content} ({doc.metadata['score']:.4f})")
        else:
            print(f"[{i + 1}] {doc.page_content}")

class RAGChain:
    def __init__(self, source_list=None):
        self.pdf = PDFRetrievalChain(source_list).create_chain()
        
        # self.retriever = self.pdf.retriever
        self.retriever = self.pdf.create_hybrid_retriever()
        self.retrieval_chain = self.pdf.chain
        self.checker_model = ChatOpenAI(temperature=0, model=StaticVariables.OPENAI_MODEL)
        self.upstage_ground_checker = UpstageGroundednessCheck()

        self.workflow = self._create_workflow()
        self.db_path = StaticVariables.SQLITE_DB_PATH
        
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self._init_database())
        else:
            asyncio.run(self._init_database())

        # ragas 평가용 데이터프레임 초기화
        self.df = pd.DataFrame({
                "question":[],
                "context":[],
                "answer":[],
                "ground_truth":[]
            })

    async def _init_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS chat_history (
                session_id TEXT, 
                role TEXT, 
                message TEXT, 
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            await db.commit()

    def _create_workflow(self):
        workflow = StateGraph(GraphState)

        # 노드추가
        workflow.add_node("question_checker", self.question_checker)
        workflow.add_node("retrieve", self.retrieve_document)
        workflow.add_node("llm_answer", self.llm_answer)
        workflow.add_node("relevance_check", self.relevance_check)
        workflow.add_node("not_found_in_context", self.not_found_in_context)
        workflow.add_node("rewrite", self.rewrite)


        # 노드 연결
        workflow.add_edge(START, "question_checker")
        
        workflow.add_conditional_edges(
            "question_checker",
            self.is_relevant,
            {
                "grounded": "retrieve",
                "notGrounded": END,
            },
        )
        
        workflow.add_edge("retrieve", "llm_answer")
        
        workflow.add_edge("llm_answer", "relevance_check")
        
        ### Upstage groundeness checker 분기 ###
        workflow.add_conditional_edges(
            "relevance_check",
            self.is_relevant,
            {
                "grounded": END,
                "notGrounded": "not_found_in_context",
                # "rewrite" : "not_found_in_context",
                # "notGrounded": "rewrite",
                "notSure": "rewrite",
            },
        )
        
        workflow.add_edge("rewrite", "retrieve")

        workflow.add_edge("not_found_in_context", END)

        
        return workflow.compile()

    
    # 지금 들어온 질문이 서비스에 맞는 쿼리인지 체크한다.
    async def question_checker(self, state: GraphState) -> GraphState:
        session_id = state["session_id"]
        chat_history = await self.get_chat_history(session_id)
        formatted_history = "\n".join(
            f"{role}: {message}" for role, message in chat_history
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system", 
                    "당신은 노동법 관련 질문을 AI 어시스턴트에 연결하는 역할입니다.\n"
                    "당신은 최고의 대한민국 노동법 전문 AI Asistant입니다 \n"
                    "사용자의 질문(Question)과 대화 기록(Chat History)을 검토하여 다음과 같이 'yes' or 'no' 로 응답하세요:\n"
                    "1. 대한민국 노동법 관련 질문: 'yes'\n"
                    "2. 직전 대화가 노동법 관련 질문이고, 추가 질문도 맥락상 노동법 관련 질문이 될 수 있는 경우('더 자세히', '잘 모르겠어' 등): 'yes'\n"
                    "3. 노동법 외 다른 법률 관련 질문: 미안함을 표현하며 친근하게 대답을 못하는 이유를 말해주세요.\n"
                    "4. 노동법 외 다른 법률 관련 질문이나 노동법과 무관한 일반 질문: 대화 기록(Chat History)기반으로 친근하게 응답하고, 어떤 도움이 필요한 지 질문해 주세요.\n"
                    "5. 노동법과 관련된 계산 질문: 바로 옆에 계산을 잘하는 AI 챗봇이 있으니, 그 쪽에 문의를 해주라는 친절히 답변을 해주세요."
                ),
                ("system", "# Chat History:\n{chat_history}\n\n"),
                ("human", "# Question:\n{question}")
            ]
        )
        chain = prompt | self.checker_model | StrOutputParser()
        response = await chain.ainvoke({"question": state["question"], "chat_history": formatted_history})
        question_check = "notGrounded"
        if response == "yes":
            question_check = "grounded"
        return GraphState(relevance=question_check, question=state["question"], answer=response)

    def not_found_in_context(self, state: GraphState) -> GraphState:
        # 우리가 건들일 수 있는 부분. 최종적으로 문서를 못찾았을 때!
        return GraphState(question=state["question"], answer="죄송합니다. 현재 제가 가진 정보로는 말씀하신 내용에 대해 정확한 답변을 드리기 어렵습니다. 혹시 노동법과 관련된 다른 궁금하신 점이 있으신가요?")


    async def retrieve_document(self, state: GraphState) -> GraphState:
        retrieved_docs = await self.retriever.ainvoke(state["question"])
        # retrieved_docs = format_docs(retrieved_docs)
        # return GraphState(context=retrieved_docs)
        formatted_context = [doc.page_content for doc in retrieved_docs]  # 리스트 형태로 변환
        return GraphState(context=formatted_context)

    async def llm_answer(self, state: GraphState) -> GraphState:
        # TODO: 들어온 세션 아이디로부터 chat_history 로드, chat_history에 저장
        session_id = state["session_id"]
        chat_history = await self.get_chat_history(session_id)
        formatted_history = "\n".join(
            f"{role}: {message}" for role, message in chat_history
        )
        response = await self.retrieval_chain.ainvoke(
            {
                "chat_history": formatted_history,
                "question": state["question"],
                "context": state["context"],
            }
        )
        return GraphState(answer=response)

    async def relevance_check(self, state: GraphState) -> GraphState:
        # response = await self.upstage_ground_checker.arun(
        #     {"context": state["context"], "answer": state["answer"]}
        # )

        # return GraphState(
        #     relevance=response, question=state["question"], answer=state["answer"]
        # )
        formatted_context = "\n\n".join([doc if isinstance(doc, str) else str(doc) for doc in state["context"]])

        # Upstage Groundedness Checker 호출
        response = await self.upstage_ground_checker.arun(
            {
                "context": formatted_context,
                "answer": state["answer"]
            }
        )

        # relevance 결과에 따라 분기
        if response == "grounded":
            relevance = "grounded"
        else:
            relevance = "notGrounded"

        return GraphState(
            relevance=relevance,
            question=state["question"],
            answer=state["answer"],
            contexts=state["context"]
        )

    ### 쿼리 재작성 노드 ###
    async def rewrite(self, state):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "당신은 전문적인 프롬프트 재작성자입니다. 현재 주어진 맥락에서 드러나지 않은 추가 정보를 얻기 위한 질문을 생성하는 것이 당신의 임무입니다.\n"
                    "당신이 생성한 질문은 관련 정보를 찾기 위해 우리의 벡터 데이터베이스를 검색하는 데 사용될 것입니다.\n"
                    "질문은 반드시 **한국어**로 작성해야 하며, 원래 질문의 의도를 유지하면서 더 구체적이고 정보를 얻기에 적합한 형태여야 합니다.\n"
                ),
                (
                    "human",
                    "다음 정보를 바탕으로 개선된 질문을 만들어주세요:\n"
                    "원래 질문: {question}\n"
                    "맥락: {context}\n"
                    "초기 답변: {answer}\n"
                    "이를 토대로 추가 정보를 얻기 위한 개선된 질문을 한국어로 작성해주세요."
                ),
            ]
        )
        model = ChatOpenAI(temperature=0, model=StaticVariables.REWRITE_MODEL)
        chain = prompt | model | StrOutputParser()
        response = await chain.ainvoke(
            {
                "question": state["question"],
                "answer": state["answer"],
                "context": state["context"],
            }
        )
        return GraphState(question=response)

    def is_relevant(self, state: GraphState) -> GraphState:
        return state["relevance"]

    ### 라우터에서 쓰는 메인함수 ###
    async def process_question(self, question: str, session_id: str):
        inputs = GraphState(question=question, session_id=session_id)
        # config = {"configurable": {"session_id": session_id}}

        # try:
        #     result = await self.workflow.ainvoke(inputs, config=config)
        #     if isinstance(result, dict) and "answer" in result:
        #         await self.update_chat_history(session_id, question, result["answer"])
        #     return result
        # except Exception as e:
        #     print(f"해당 질문을 처리하는 데 실패했습니다.: {str(e)}")
        #     return None
        try:
            result = await self.workflow.ainvoke(inputs)
            if isinstance(result, dict) and "answer" in result:
                await self.update_chat_history(session_id, question, result["answer"])

                # 컨텍스트가 없으면 빈리스트 제공
                contexts = result.get("context",[])
                if not contexts:
                    contexts = [""]

                # 데이터프레임에 일관된 길이의 데이터 추가  
                self.df = pd.concat([self.df, pd.DataFrame({
                    "question": [question],
                    "answer": [result["answer"]],
                    "contexts": [contexts],
                    "ground_truth": ["기본 정답입니다."]
                })], ignore_index=True)

            # 데이터셋 생성후 평가
            eval_data = Dataset.from_dict(self.df)
            ragas_result = await self.run_ragas_evaluation(eval_data)

            print(f"\n\nRAGAS 평가 결과:\n{ragas_result}")
            return result

        except Exception as e:
            print(f"해당 질문을 처리하는 데 실패했습니다.: {str(e)}")
            return None

   

    async def run_ragas_evaluation(self, eval_data):
        """RAGAS 평가 실행 및 결과 출력"""
        print("RAGAS 평가를 실행합니다...")  # 디버깅 메시지 추가

        # RAGAS 평가 실행
        result = evaluate(
            dataset=eval_data,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                # context_recall,
            ]
        )

        # 결과를 판다스 데이터프레임으로 변환 및 출력
        result_df = result.to_pandas()
        print(f"\nRAGAS 평가 점수:\n{result_df}")  # 터미널 출력

        return result_df  # 데이터프레임 반환

    ### 히스토리 관리용 메소드들 ###
    async def get_chat_history(self, session_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT role, message FROM (SELECT role, message, timestamp FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10) sub ORDER BY timestamp ASC",
                (session_id,),
            ) as cursors:
                result = await cursors.fetchall()
                for node in result:
                    print(f"node: {node}")
        return result

    async def update_chat_history(self, session_id: str, question: str, answer: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO chat_history (session_id, role, message) VALUES (?,?,?)",
                (session_id, "user", question),
            )
            await db.execute(
                "INSERT INTO chat_history (session_id, role, message) VALUES (?,?,?)",
                (session_id, "assistant", answer),
            )
            await db.commit()

    # 히스토리 삭제용 메소드. 필요할 때 수정 후 사용
    async def clear_chat_history(self, session_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM chat_history WHERE session_id = ?", (session_id,)
            )
            await db.commit()
