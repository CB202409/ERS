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


class RAGChain:
    def __init__(self, source_list):
        self.pdf = PDFRetrievalChain(source_list).create_chain(False)
        self.pdf_retriever = self.pdf.retriever
        self.pdf_chain = self.pdf.chain
        self.upstage_ground_checker = UpstageGroundednessCheck()

        self.workflow = self._create_workflow()

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
        response = self.pdf_chain.invoke(
            {"question": state["question"], "context": state["context"]}
        )
        return GraphState(answer=response)

    def relevance_check(self, state: GraphState) -> GraphState:
        response = self.upstage_ground_checker.run(
            {"context": state["context"], "answer": state["answer"]}
        )
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

    async def process_question(self, question: str):
        inputs = GraphState(question=question)
        results = []
        for output in self.workflow.stream(inputs):
            results.append(output)
        return results
