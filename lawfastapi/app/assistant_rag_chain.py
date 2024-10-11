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


class AssistantRAGChain:
    # source_list는 의미없는 값이니까 신경쓰지마시죠
    def __init__(self, source_list=None):
        
        self.checker_model = ChatOpenAI(temperature=0, model=StaticVariables.OPENAI_MODEL)

        self.workflow = self._create_workflow()
        self.db_path = StaticVariables.SQLITE_DB_PATH
        asyncio.run(self._init_database())

    async def _init_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS chat_history_cal (
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

        workflow.add_node("llm_checker", self.question_checker)  # 어시스턴트에 넘길 지 판단하는 녀석
        workflow.add_node("assistant_llm", self.assistant_llm)  # 전달받은 인자를 통해 계산

        workflow.add_conditional_edges(
            "question_checker",
            self.is_relevant,
            {
                "grounded": "assistant_llm",
                "notGrounded": END,
            },
        )

        workflow.set_entry_point("retrieve")

        return workflow.compile()

    
    # 지금 들어온 질문이 서비스에 맞는 쿼리인지 체크한다.(슬롯필링은 여기서!)
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
                    "당신은 고용노동법 계산 관련 질문을 AI 어시스턴트에 연결하는 역할입니다.\n"
                    "사용자의 질문(Question)과 대화 기록(Chat History)을 검토하여 슬 롯 필 링!:\n"
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


    async def assistant_llm(self, state: GraphState) -> GraphState:
        # TODO: 들어온 세션 아이디로부터 chat_history 로드, chat_history에 저장
        session_id = state["session_id"]
        chat_history = await self.get_chat_history(session_id)
        formatted_history = "\n".join(
            f"{role}: {message}" for role, message in chat_history
        )
        # 아래 형태로 실행
        response = await self.retrieval_chain.ainvoke(
            {
                "chat_history": formatted_history,
                "question": state["question"],
                "context": state["context"],
            }
        )
        return GraphState(answer=response)




    ### AI 진입 포인트로 쓰는 메인함수 ###
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
                "SELECT role, message FROM (SELECT role, message, timestamp FROM chat_history_cal WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10) sub ORDER BY timestamp ASC",
                (session_id,),
            ) as cursors:
                result = await cursors.fetchall()
                for node in result:
                    print(f"node: {node}")
        return result

    async def update_chat_history(self, session_id: str, question: str, answer: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO chat_history_cal (session_id, role, message) VALUES (?,?,?)",
                (session_id, "user", question),
            )
            await db.execute(
                "INSERT INTO chat_history_cal (session_id, role, message) VALUES (?,?,?)",
                (session_id, "assistant", answer),
            )
            await db.commit()

    # 히스토리 삭제용 메소드. 필요할 때 수정 후 사용
    async def clear_chat_history(self, session_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM chat_history_cal WHERE session_id = ?", (session_id,)
            )
            await db.commit()
