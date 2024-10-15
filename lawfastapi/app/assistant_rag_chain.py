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
from langchain_experimental.openai_assistant import OpenAIAssistantRunnable
import aiosqlite
import asyncio
from openai import OpenAI
import time


class AssistantRAGChain:
    # source_list는 의미없는 값이니까 신경쓰지마시죠
    def __init__(self, client: OpenAI):
        
        self.checker_model = ChatOpenAI(temperature=0, model="gpt-4o-mini")

        self.workflow = self._create_workflow()
        self.db_path = StaticVariables.SQLITE_DB_PATH
        self.client = client
        
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self._init_database())
        else:
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

        # 노드 추가
        workflow.add_node("question_checker", self.question_checker)  # 어시스턴트에 넘길 지 판단하는 녀석
        workflow.add_node("assistant_llm", self.assistant_llm)  # 전달받은 인자를 통해 계산

        # 노드 연결
        workflow.add_edge(START, "question_checker")

        workflow.add_conditional_edges(
            "question_checker",
            self.is_relevant,
            {
                "grounded": "assistant_llm",
                "notGrounded": END,
            },
        )
        
        workflow.add_edge("assistant_llm", END)


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
                    "당신은 고용노동법 관련 계산 질문을 AI 어시스턴트에 연결하는 역할입니다.\n"
                    "사용자의 질문(Question)과 대화 기록(Chat History)을 검토하여 다음과 같이 응답하세요:\n"
                    "1. 실업급여, 최저임금, 퇴직금 등 고용노동법 관련 계산 질문: 다른 사족없이 짧게 'yes' 라고 대답하세요.\n"
                    "2. 고용노동법 외 다른 법률 관련 질문: 미안함을 표현하며 친근하게 대답을 못하는 이유를 말해주세요.\n"
                    "3. 고용노동법 관련 임금 계산과 무관한 질문: 바로 옆에 법적 자문을 잘하는 AI 챗봇이 있으니, 그 쪽에 문의를 해주라는 친절히 답변을 해주세요."
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
        # 어시스턴트와 쓰레드가 있는 지 확인
        try:
            self.client.beta.assistants.retrieve(assistant_id=StaticVariables.OPENAI_ASSISTANT_ID)
        except Exception as e:
            return GraphState(answer="어시스턴트 아이디가 엄서용 . . .")
        try:
            self.client.beta.threads.retrieve(thread_id=StaticVariables.OPENAI_THREAD_ID)
        except Exception as e:
            return GraphState(answer="쓰레드가 존재하지 안아용 . . .")
        
        # TODO: 들어온 세션 아이디로부터 chat_history 로드, chat_history에 저장
        session_id = state["session_id"]
        chat_history = await self.get_chat_history(session_id)
        formatted_history = "\n".join(
            f"{role}: {message}" for role, message in chat_history
        )
        
       # 어시스턴트의 설정 업데이트
        self.client.beta.assistants.update(
            assistant_id=StaticVariables.OPENAI_ASSISTANT_ID,
            name = StaticVariables.OPENAI_ASSISTANT_NAME,
            model = StaticVariables.OPENAI_ASSISTANT_MODEL,            
            temperature = StaticVariables.OPENAI_ASSISTANT_TEMPERATURE,
            top_p = StaticVariables.OPENAI_ASSISTANT_TOP_P,
            tools = [{"type": "code_interpreter"}],
            instructions = (
                "무조건 존댓말 해야해. 너는 최저임금만 계산할 수 있어.\n"
                "코드인터프리터를 이용해서 계산을 해. 근무시간, 주휴수당 등의 요소가 빠져있으면 평균적인 값을 이용하도록 해.\n"
                "계산을 끝난 후 대답할 때에는 계산을 어떻게 했는지에 대해 설명해주어야 해."
                "말 끝에는 이모지를 추가해\n"
                "대답은 아래 대화내용에 맞게 답해야해\n"
                "# 대화내용\n"
                f"{formatted_history}\n"
                "----- 대화내용 끝 -----"
            ),
        )
        
        # 메시지 추가
        message = self.client.beta.threads.messages.create(
            thread_id = StaticVariables.OPENAI_THREAD_ID,
            role = "user",
            content = state["question"]
        )
        
        # 쓰레드 실행
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id = StaticVariables.OPENAI_THREAD_ID,
            assistant_id= StaticVariables.OPENAI_ASSISTANT_ID
        )
        
        timeout = 10
        elapsed_time = 0
        
        while run.status != "completed" and elapsed_time < timeout:
            time.sleep(1)
            elapsed_time += 1
            print("시간경과: ", elapsed_time, "초")
            run = self.client.beta.threads.runs.poll(run.id)
        
        if run.status == "completed":
            messages = self.client.beta.threads.messages.list(limit=10 ,thread_id=StaticVariables.OPENAI_THREAD_ID)
            
            result = messages.data[0].content[0].text.value
            
            # 메시지삭제
            self.client.beta.threads.messages.delete(thread_id=StaticVariables.OPENAI_THREAD_ID, message_id=messages.data[0].id)
            self.client.beta.threads.messages.delete(thread_id=StaticVariables.OPENAI_THREAD_ID, message_id=messages.data[1].id)    

            return GraphState(answer=result)                
        else:
            return GraphState(answer="어시스턴트를 돌리는 데 문제가 생긴 것 같네요")
       


    def is_relevant(self, state: GraphState) -> GraphState:
        return state["relevance"]


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
