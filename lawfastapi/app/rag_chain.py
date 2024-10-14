import aiosqlite.context
from retrieval_chain.pdf import PDFRetrievalChain
from retrieval_chain.utils import format_docs
from schema.graph_state import GraphState
from langchain_upstage import UpstageGroundednessCheck
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, StateGraph
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
        if source_list is None:
            self.pdf = PDFRetrievalChain(source_list).create_chain(False)
        else:
            print(
                f"Pinecone의 {StaticVariables.PINECONE_NAMESPACE}에 문서를 저장합니다:\n",
                source_list,
            )
            print("VDB에 중복된 데이터를 넣고 있는 지 확인하세요!")
            self.pdf = PDFRetrievalChain(source_list).create_chain(True)
        # self.retriever = self.pdf.retriever
        self.retriever = self.pdf.create_hybrid_retriever()

        self.retrieval_chain = self.pdf.chain
        self.upstage_ground_checker = UpstageGroundednessCheck()

        self.workflow = self._create_workflow()
        self.db_path = StaticVariables.SQLITE_DB_PATH
        asyncio.run(self._init_database())

        # ragas 평가용 데이터프레임 초기화
        self.df = pd.DataFrame({
                "question": [],
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

        workflow.add_node("retrieve", self.retrieve_document)
        workflow.add_node("llm_answer", self.llm_answer)
        workflow.add_node("relevance_check", self.relevance_check)
        workflow.add_node("rewrite", self.rewrite)

        workflow.add_edge("retrieve", "llm_answer")
        workflow.add_edge("llm_answer", "relevance_check")
        workflow.add_edge("rewrite", "retrieve")

        workflow.add_conditional_edges(
            "relevance_check",
            self.is_relevant,
            {
                "grounded": END,
                "notGrounded": "rewrite",
                "notSure": "rewrite",
            },
        )

        workflow.set_entry_point("retrieve")

        return workflow.compile()

    
    ### 멀티턴? ###
    # 초기 질문이 법률 관련 질문인지 아닌지 확인하고, 그에 따라서 다른 함수로 넘어감
    # def llm_answer(self, state: GraphState) -> GraphState:
    #     if self.is_legal_question(state["question"]):
    #         answer = self.llm_legal_answer(state)
    #     else:
    #         answer = self.llm_non_legal_answer(state)
    #     return GraphState(answer=answer)

    async def retrieve_document(self, state: GraphState) -> GraphState:
        # retrieved_docs = await self.retriever.ainvoke(state["question"])
        # retrieved_docs = format_docs(retrieved_docs)
        # return GraphState(context=retrieved_docs)
        retrieved_docs = await self.retriever.ainvoke(state["question"])
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
        eval_data = Dataset.from_dict({
        "question": [state["question"]],
        "contexts": [[doc for doc in state["context"]]],  # 2D 리스트로 전달
        "answer": [state["answer"]],
        "ground_truth": ["기본 정답입니다."]
        })

        ragas_result = await self.run_ragas_evaluation(eval_data)

        # 평가 점수를 바탕으로 relevance 판단
        if ragas_result["answer_relevancy"].iloc[0] < 1:
            relevance = "grounded"
        else:
            relevance = "notGrounded"

        return GraphState(
            relevance=relevance,
            question=state["question"],
            answer=state["answer"],
            context=state["context"]
        )   

    async def rewrite(self, state):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a professional prompt rewriter. Your task is to generate the question in order to get additional information that is now shown in the context."
                    "Your generated question will be searched on the web to find relevant information.",
                    "You explain things clearly when answering questions to users.",
                    "Additionally, if you find material, you will be notified of the source of that material."

                ),
                (
                    "human",
                    "Rewrite the question to get additional information to get the answer."
                    "\n\nHere is the initial question:\n ------- \n{question}\n ------- \n"
                    "\n\nHere is the initial context:\n ------- \n{context}\n ------- \n"
                    "\n\nHere is the initial answer to the question:\n ------- \n{answer}\n ------- \n"
                    "\n\nFormulate an improved question in Korean:",
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

    async def process_question(self, question: str, session_id: str):
        inputs = GraphState(question=question, session_id=session_id)

        try:
            result = await self.workflow.ainvoke(inputs)
            if isinstance(result, dict) and "answer" in result:
                await self.update_chat_history(session_id, question, result["answer"])

                contexts = [doc for doc in result.get("context", [])]  # 리스트로 처리
                self.df = pd.concat([self.df, pd.DataFrame({
                    "question": [question],
                    "answer": [result["answer"]],
                    "contexts": [contexts],
                    "ground_truth": ["기본 정답입니다."]
                })], ignore_index=True)

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
                context_recall,
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
