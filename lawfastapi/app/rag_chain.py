import aiosqlite.context
from retrieval_chain.pdf import PDFRetrievalChain
from retrieval_chain.utils import format_docs, format_searched_docs
from schema.graph_state import GraphState
from langchain_upstage import UpstageGroundednessCheck
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from config.static_variables import StaticVariables
from typing import Dict, List, Tuple
import aiosqlite
import json
import asyncio


class RAGChain:
    def __init__(self, source_list = None):
        if source_list is None:
            self.pdf = PDFRetrievalChain(source_list).create_chain(False)
        else:
            print(f"Pinecone의 {StaticVariables.PINECONE_NAMESPACE}에 문서를 저장합니다:\n", source_list)
            print("VDB에 중복된 데이터를 넣고 있는 지 확인하세요!")
            self.pdf = PDFRetrievalChain(source_list).create_chain(True)
        self.retriever = self.pdf.retriever
        self.retrieval_chain = self.pdf.chain
        self.upstage_ground_checker = UpstageGroundednessCheck()
        
        self.workflow = self._create_workflow()
        self.memory = MemorySaver()
        self.db_path = StaticVariables.SQLITE_DB_PATH
        asyncio.run(self._init_database())
        
    async def _init_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS chat_history (
                session_id TEXT PRIMARY KEY, 
                history TEXT, 
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
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
        retrieved_docs = await self.retriever.ainvoke(state["question"])
        retrieved_docs = format_docs(retrieved_docs)
        return GraphState(context=retrieved_docs)

    async def llm_answer(self, state: GraphState) -> GraphState:
        # TODO: 들어온 세션 아이디로부터 chat_history 로드, chat_history에 저장
        session_id = state["session_id"]
        chat_history = await self.get_chat_history(session_id)
        response = await self.retrieval_chain.ainvoke(
            {"chat_history": chat_history, "question": state["question"], "context": state["context"]}
        )
        return GraphState(answer=response)

    async def relevance_check(self, state: GraphState) -> GraphState:
        response = await self.upstage_ground_checker.arun(
            {"context": state["context"], "answer": state["answer"]}
        )
         
        
        return GraphState(
            relevance=response, question=state["question"], answer=state["answer"]
        )

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
        response = chain.ainvoke(
            {
                "question": state["question"],
                "answer": state["answer"],
                "context": state["context"],
            }
        )
        return GraphState(question=response)

    def is_relevant(self, state: GraphState) -> GraphState:
        return state["relevance"]
    
    async def get_chat_history(self, session_id: str) -> List[Tuple[str, str]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT history FROM chat_history WHERE session_id = ?", (session_id,)) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    try:
                        return json.loads(result[0])
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON for session {session_id}. Returning empty history.")
                        print("ERR: ", e)
                        return []
        return []
    
    async def update_chat_history(self, session_id: str, question: str, answer: str):
        history = await self.get_chat_history(session_id)
        history_store_question = f"User: {question}"
        history_store_answer = f"AI: {answer}"
        history.append((history_store_question, history_store_answer))
        
        history_json = json.dumps(history)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO chat_history (session_id, history) VALUES (?,?)", (session_id, history_json))
            await db.commit()
            
        

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

    # 히스토리 삭제용 메소드. 필요할 때 수정 후 사용
    async def clear_chat_history(self, session_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
            await db.commit()