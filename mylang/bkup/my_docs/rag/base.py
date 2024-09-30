from langchain import hub
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_upstage import UpstageEmbeddings
from langchain_openai import ChatOpenAI

from langchain_core.output_parsers import StrOutputParser
from abc import ABC, abstractmethod
from operator import itemgetter

from langchain.prompts import ChatPromptTemplate


UPSTAGE_EMBEDDING_MODEL = "solar-embedding-1-large"
OPENAI_MODEL = "gpt-4o-mini"

class RetrievalChain(ABC):
    def __init__(self):
        self.source_uri = None
        self.k = 5

    @abstractmethod
    def load_documents(self, source_uris):
        """loader를 사용하여 문서를 로드합니다."""
        pass

    @abstractmethod
    def create_text_splitter(self):
        """text splitter를 생성합니다."""
        pass

    def split_documents(self, docs, text_splitter):
        """text splitter를 사용하여 문서를 분할합니다."""
        return text_splitter.split_documents(docs)

    def create_embedding(self):
        return UpstageEmbeddings(model=UPSTAGE_EMBEDDING_MODEL)

    def create_vectorstore(self, split_docs):
        return FAISS.from_documents(
            documents=split_docs, embedding=self.create_embedding()
        )

    def create_retriever(self, vectorstore):
        # MMR을 사용하여 검색을 수행하는 retriever를 생성합니다.
        dense_retriever = vectorstore.as_retriever(
            search_type="mmr", search_kwargs={"k": self.k}
        )
        return dense_retriever

    def create_model(self):
        return ChatOpenAI(model_name=OPENAI_MODEL, temperature=0)

    # def create_prompt(self):
    #     return hub.pull("teddynote/rag-korean-with-source")

    def create_prompt(self):
        prompt = ChatPromptTemplate.from_template(
          "당신은 질문-답변(Question-Answering)을 수행하는 친절한 AI 어시스턴트입니다. 당신의 임무는 주어진 문맥(context) 에서 주어진 질문(question) 에 답하는 것입니다.\n"
          "검색된 다음 문맥(context) 을 사용하여 질문(question) 에 답하세요.\n"
          "기술적인 용어나 이름은 번역하지 않고 그대로 사용해 주세요. 출처(page, source)를 답변에 포함하세요. 검색 정보라면 출처(source)만 답변에 포함하세요. 답변은 한글로 답변해 주세요.\n"
          "\n\n"
          "HUMAN "
          "#Question: "
          "{question}"
          "\n\n"
          "#Context: "
          "{context}"
          "\n\n"
          "#Answer: "
        )
        return prompt

    @staticmethod
    def format_docs(docs):
        return "\n".join(docs)

    def create_chain(self):
        docs = self.load_documents(self.source_uri)
        text_splitter = self.create_text_splitter()
        split_docs = self.split_documents(docs, text_splitter)
        self.vectorstore = self.create_vectorstore(split_docs)
        self.retriever = self.create_retriever(self.vectorstore)
        model = self.create_model()
        prompt = self.create_prompt()
        self.chain = (
            {"question": itemgetter("question"), "context": itemgetter("context")}
            | prompt
            | model
            | StrOutputParser()
        )
        return self
