from langchain_core.output_parsers import StrOutputParser
from langchain_upstage import UpstageEmbeddings
from langchain_openai import ChatOpenAI

from abc import ABC, abstractmethod
from operator import itemgetter

from langchain.prompts import ChatPromptTemplate

# 파인콘
from langchain_teddynote.korean import stopwords
from langchain_teddynote.community.pinecone import (
    create_sparse_encoder,
    fit_sparse_encoder,
    preprocess_documents,
    upsert_documents_parallel,
    init_pinecone_index,
    PineconeKiwiHybridRetriever,
)
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore

# 히스토리
from langgraph.checkpoint.memory import MemorySaver
from config.static_variables import StaticVariables

import os


class RetrievalChain(ABC):
    def __init__(self, memory: MemorySaver):
        self.source_uri = None
        self.memory = memory

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

    def create_dense_embedding(self):
        return UpstageEmbeddings(model=StaticVariables.UPSTAGE_EMBEDDING_MODEL)

    # 벡터스토어 로드. 인덱스는 미리 만들어 두는 것을 상정함
    def pinecone_load_vectorstore(self):
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(StaticVariables.PINECONE_INDEX_NAME)
        vectorstore = PineconeVectorStore(
            index=index,
            embedding=UpstageEmbeddings(model=StaticVariables.UPSTAGE_EMBEDDING_MODEL),
            namespace=StaticVariables.PINECONE_NAMESPACE,
        )
        return vectorstore

    def pincone_hybrid_upsert(self, split_docs):
        # 파인콘 인덱스 로드
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        pc_index = pc.Index("law-pdf")

        # 문서 전처리
        contents, metadatas = preprocess_documents(
            split_docs=split_docs,
            metadata_keys=["source", "page", "total_pages"],
            use_basename=True,
        )

        # sparse 인코더 생성
        sparse_encoder = create_sparse_encoder(stopwords(), mode="kiwi")
        saved_path = fit_sparse_encoder(
            sparse_encoder=sparse_encoder,
            contents=contents,
            save_path=StaticVariables.SPARSE_ENCODER_PKL_PATH,
        )
        # sparse 인코더 로드(나중에 필요)
        # sparse_encoder = load_sparse_encoder(StaticVariables.SPARSE_ENCODER_PKL_PATH)

        upstage_embeddings = UpstageEmbeddings(model=StaticVariables.UPSTAGE_EMBEDDING_MODEL)

        upsert_documents_parallel(
            index=pc_index,
            namespace=StaticVariables.PINECONE_NAMESPACE,
            contents=contents,
            metadatas=metadatas,
            sparse_encoder=sparse_encoder,
            embedder=upstage_embeddings,
            batch_size=32,
            max_workers=30,
        )

    def create_hybrid_retriever(self):
        pinecone_params = init_pinecone_index(
            index_name=StaticVariables.PINECONE_INDEX_NAME,  # Pinecone 인덱스 이름
            namespace=StaticVariables.PINECONE_NAMESPACE,  # Pinecone Namespace
            api_key=os.environ["PINECONE_API_KEY"],  # Pinecone API Key
            sparse_encoder_path=StaticVariables.SPARSE_ENCODER_PKL_PATH,  # Sparse Encoder 저장경로(save_path)
            stopwords=stopwords(),  # 불용어 사전
            tokenizer="kiwi",
            embeddings=UpstageEmbeddings(
                model=StaticVariables.UPSTAGE_RETRIEVE_MODEL
            ),  # Dense Embedder
            top_k=StaticVariables.RETRIEVAL_K,  # Top-K 문서 반환 개수
            alpha=StaticVariables.RETRIEVAL_ALPHA,  # alpha=0.75로 설정한 경우, (0.75: Dense Embedding, 0.25: Sparse Embedding)
        )
        return PineconeKiwiHybridRetriever(**pinecone_params)

    def create_model(self):
        return ChatOpenAI(model_name=StaticVariables.OPENAI_MODEL, temperature=0)

    def create_prompt(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system", 
                    "당신은 질문-답변(Question-Answering)을 수행하는 법률 전문 AI 어시스턴트입니다. 주어진 문맥(context)과 대화 기록(chat history)을 바탕으로 주어진 질문(question)에 답하세요.\n"
                    "다음 지침을 엄격히 따라주세요:\n"
                    "1. 검색된 문맥(context)과 대화 기록(chat history)을 신중히 분석하여 질문(question)에 답하세요.\n"
                    "2. 답변을 찾을 수 없는 경우: '주어진 정보에서 해당 질문에 대한 답변을 찾을 수 없습니다. 다른 질문이 있으시면 말씀해 주세요.'라고 정중히 답하세요.\n"
                    "3. 답변 수준: 중학생이 이해할 수 있는 명확하고 간결한 언어로 설명하세요.\n"
                    "4. 출처 표기: 답변에 사용된 정보의 출처(문서명, 법 조항)를 명확히 제시하세요. 예: '(출처: 민법 제1조)'\n"
                    "5. 언어: 모든 답변은 한글로 작성하세요.\n"
                    "6. 일관성: 이전 대화 내용을 참조하여 일관된 답변을 제공하세요. 이전 답변과 모순되지 않도록 주의하세요.\n"
                    "7. 후속 질문 대응: 사용자의 추가 질문이나 설명 요청에 적절히 대응하세요. 필요시 더 자세한 설명을 요청하세요.\n"
                    "8. 맥락 유지: 대화가 진행되어도 초기에 제공된 맥락을 계속 참조하세요. 필요시 이전 정보를 요약하여 제시하세요.\n"
                    "9. 불확실성 표현: 확실하지 않은 정보에 대해서는 '~로 추정됩니다', '~일 가능성이 있습니다' 등의 표현을 사용하세요.\n"
                    "10. 법률 조언 제한: 구체적인 법률 조언이 필요한 경우, 전문 변호사와 상담을 권유하세요.\n"
                ),
                ("system", "Context:\n{context}"),
                ("system", "Chat History:\n{chat_history}"),
                ("human", "Question: {question}\n\n")
            ]
        )
        return prompt

    @staticmethod
    def format_docs(docs):
        return "\n".join(docs)

    def write_pinecone_with_docs(self, source_uri):
        docs = self.load_documents(source_uri)
        text_splitter = self.create_text_splitter()
        split_docs = self.split_documents(docs, text_splitter)
        self.pincone_hybrid_upsert(split_docs)  # 문서 벡터DB에 저장

    def create_chain(self, is_docs_input=False):
        self.vectorstore = self.pinecone_load_vectorstore()  # 파인콘 로드

        # 파인콘에 문서 업로드
        if is_docs_input == True:
            self.write_pinecone_with_docs(self.source_uri)

        # 파인콘 검색기 객체 생성
        self.retriever = self.create_hybrid_retriever()

        model = self.create_model()
        prompt = self.create_prompt()
        self.chain = (
            {
                "chat_history": itemgetter("chat_history"),
                "question": itemgetter("question"),
                "context": itemgetter("context"),
            }
            | prompt
            | model
            | StrOutputParser()
        )
        return self
