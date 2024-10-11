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


class RAGChain:
    def __init__(self, source_list=None):
        self.pdf = PDFRetrievalChain(source_list).create_chain()
        
        self.retriever = self.pdf.retriever
        self.retrieval_chain = self.pdf.chain
        self.checker_model = ChatOpenAI(temperature=0, model=StaticVariables.OPENAI_MODEL)
        self.upstage_ground_checker = UpstageGroundednessCheck()

        self.workflow = self._create_workflow()
        self.db_path = StaticVariables.SQLITE_DB_PATH
        asyncio.run(self._init_database())

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

        workflow.add_node("question_checker", self.question_checker)
        workflow.add_node("retrieve", self.retrieve_document)
        workflow.add_node("llm_answer", self.llm_answer)
        workflow.add_node("relevance_check", self.relevance_check)
        workflow.add_node("not_found_in_context", self.not_found_in_context)
        workflow.add_node("rewrite", self.rewrite)


        workflow.add_edge("retrieve", "llm_answer")
        workflow.add_edge("llm_answer", "relevance_check")
        workflow.add_edge("rewrite", "retrieve")

        workflow.add_edge("not_found_in_context", END)

        workflow.add_conditional_edges(
            "question_checker",
            self.is_relevant,
            {
                "grounded": "retrieve",
                "notGrounded": END,
            },
        )
        
        
        ### Upstage groundeness checker 분기 ###
        workflow.add_conditional_edges(
            "relevance_check",
            self.is_relevant,
            {
                "grounded": END,
                "notGrounded": "not_found_in_context",
                "notSure": "rewrite",
            },
        )
        

        workflow.set_entry_point("question_checker")

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
                    "당신은 고용노동법 관련 질문을 AI 어시스턴트에 연결하는 역할입니다.\n"
                    "사용자의 질문(Question)과 대화 기록(Chat History)을 검토하여 다음과 같이 응답하세요:\n"
                    "1. 고용복지, 근로기준, 노사관계, 산업안전 등 고용노동법 관련 질문: 'yes'\n"
                    "2. 직전 대화가 고용노동법 관련 질문이고, 추가 질문도 맥락상 고용노동법 관련 질문이 될 수 있는 경우(예: '더 자세히', '잘 모르겠어' 등): : 'yes'\n"
                    "3. 고용노동법 외 다른 법률 관련 질문: 미안함을 표현하며 친근하게 대답을 못하는 이유를 말해주세요.\n"
                    "4. 고용노동법 외 다른 법률 관련 질문이나 고용노동법과 무관한 일반 질문: 대화 기록(Chat History)기반으로 친근하게 응답하고, 어떤 도움이 필요한 지 질문해 주세요.\n"
                    "5. 고용노동법과 관련된 계산 질문: 바로 옆에 계산을 잘하는 AI 챗봇이 있으니, 그 쪽에 문의를 해주라는 친절히 답변을 해주세요."
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
        return GraphState(question=state["question"], answer="해당 내용에 대한 정보가 없습니다. 다른 질문을 부탁드립니다.")


    async def retrieve_document(self, state: GraphState) -> GraphState:
        retrieved_docs = await self.retriever.ainvoke(state["question"])
        retrieved_docs = format_docs(retrieved_docs)
        return GraphState(context=retrieved_docs)

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
        response = await self.upstage_ground_checker.arun(
            {"context": state["context"], "answer": state["answer"]}
        )

        return GraphState(
            relevance=response, question=state["question"], answer=state["answer"]
        )

    ### 쿼리 재작성 노드 ###
    async def rewrite(self, state):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a professional prompt rewriter. Your task is to generate the question in order to get additional information that is now shown in the context."
                    "Your generated question will be searched on the web to find relevant information.",
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

    ### 라우터에서 쓰는 메인함수 ###
    async def process_question(self, question: str, session_id: str):
        inputs = GraphState(question=question, session_id=session_id)
        config = {"configurable": {"session_id": session_id}}

        try:
            result = await self.workflow.ainvoke(inputs, config=config)
            if isinstance(result, dict) and "answer" in result:
                await self.update_chat_history(session_id, question, result["answer"])
            return result
        except Exception as e:
            print(f"해당 질문을 처리하는 데 실패했습니다.: {str(e)}")
            return None

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
