from rag.pdf import PDFRetrievalChain
from rag.utils import format_docs, format_searched_docs
from app.models import GraphState
from langchain_upstage import UpstageGroundednessCheck
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from app.static_variables import Static_variables
from typing import Dict, List, Tuple


class RAGChain:
    def __init__(self, source_list):
        self.pdf = PDFRetrievalChain(source_list).create_chain(False)
        self.pdf_retriever = self.pdf.retriever
        self.pdf_chain = self.pdf.chain
        self.upstage_ground_checker = UpstageGroundednessCheck()
        
        self.workflow = self._create_workflow()
        self.memory = MemorySaver()
        self.chat_model = ChatOpenAI(temperature=0, model=Static_variables.OPENAI_MODEL)  # ?
        self.chat_histories: Dict[str, List[Tuple[str, str]]] = {}

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

    def retrieve_document(self, state: GraphState) -> GraphState:
        retrieved_docs = self.pdf_retriever.invoke(state["question"])
        retrieved_docs = format_docs(retrieved_docs)
        return GraphState(context=retrieved_docs)

    def llm_answer(self, state: GraphState) -> GraphState:
        # TODO: 들어온 세션 아이디로부터 chat_history 로드, chat_history에 저장
        session_id = state["session_id"]
        chat_history = self.get_chat_history(session_id)
        
        response = self.pdf_chain.invoke(
            {"chat_history": chat_history, "question": state["question"], "context": state["context"]}
        )
        
        
        return GraphState(answer=response)

    def relevance_check(self, state: GraphState) -> GraphState:
        response = self.upstage_ground_checker.run(
            {"context": state["context"], "answer": state["answer"]}
        )
        
        
        if response == "grounded":
            session_id = state["session_id"]
            self.update_chat_history(session_id, state["question"], response)        
        
        return GraphState(
            relevance=response, question=state["question"], answer=state["answer"]
        )

    def rewrite(self, state):
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
        model = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        chain = prompt | model | StrOutputParser()
        response = chain.invoke(
            {
                "question": state["question"],
                "answer": state["answer"],
                "context": state["context"],
            }
        )
        return GraphState(question=response)

    def is_relevant(self, state: GraphState) -> GraphState:
        return state["relevance"]
    
    def get_chat_history(self, session_id: str) -> List[Tuple[str, str]]:
        return self.chat_histories.get(session_id, [])
    
    def update_chat_history(self, session_id: str, question: str, answer: str):
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = []
        self.chat_histories[session_id].append((question, answer))

    def process_question(self, question: str, session_id: str):
        inputs = GraphState(question=question, session_id=session_id, first_question=question)
        config = {"configurable": {"session_id": session_id}}
        
        try:
            result = self.workflow.invoke(inputs, config=config)
            return result
        except Exception as e:
            print(f"해당 질문을 처리하는 데 실패했습니다.: {str(e)}")
            return None

    # 히스토리 삭제용 메소드. 필요할 때 수정 후 사용
    def clear_chat_history(self, session_id: str):
        if session_id in self.chat_histories:
            del self.chat_histories[session_id]