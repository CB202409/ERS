from langchain import hub
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_upstage import UpstageEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

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

import os


UPSTAGE_EMBEDDING_MODEL = "solar-embedding-1-large"
UPSTAGE_RETRIEVE_MODEL = "solar-embedding-1-large-query"
OPENAI_MODEL = "gpt-4o-mini"
PINECONE_INDEX_NAME = "law-pdf"
PINECONE_NAMESPACE = "ns1"
SPARSE_ENCODER_PKL_PATH = "../sparse_encoder.pkl"


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

    def create_dense_embedding(self):
        return UpstageEmbeddings(model=UPSTAGE_EMBEDDING_MODEL)

    # 벡터스토어 로드. 인덱스는 미리 만들어 두는 것을 상정함
    def pinecone_load_vectorstore(self):
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(PINECONE_INDEX_NAME)
        vectorstore = PineconeVectorStore(
            index=index,
            embedding=UpstageEmbeddings(model=UPSTAGE_EMBEDDING_MODEL),
            namespace=PINECONE_NAMESPACE,
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
            save_path=SPARSE_ENCODER_PKL_PATH,
        )
        # sparse 인코더 로드(나중에 필요)
        # sparse_encoder = load_sparse_encoder(SPARSE_ENCODER_PKL_PATH)

        upstage_embeddings = UpstageEmbeddings(model=UPSTAGE_EMBEDDING_MODEL)

        upsert_documents_parallel(
            index=pc_index,
            namespace=PINECONE_NAMESPACE,
            contents=contents,
            metadatas=metadatas,
            sparse_encoder=sparse_encoder,
            embedder=upstage_embeddings,
            batch_size=32,
            max_workers=30,
        )

    def create_hybrid_retriever(self):
        pinecone_params = init_pinecone_index(
            index_name=PINECONE_INDEX_NAME,  # Pinecone 인덱스 이름
            namespace=PINECONE_NAMESPACE,  # Pinecone Namespace
            api_key=os.environ["PINECONE_API_KEY"],  # Pinecone API Key
            sparse_encoder_path=SPARSE_ENCODER_PKL_PATH,  # Sparse Encoder 저장경로(save_path)
            stopwords=stopwords(),  # 불용어 사전
            tokenizer="kiwi",
            embeddings=UpstageEmbeddings(
                model=UPSTAGE_RETRIEVE_MODEL
            ),  # Dense Embedder
            top_k=5,  # Top-K 문서 반환 개수
            alpha=0.5,  # alpha=0.75로 설정한 경우, (0.75: Dense Embedding, 0.25: Sparse Embedding)
        )
        return PineconeKiwiHybridRetriever(**pinecone_params)

    def create_model(self):
        return ChatOpenAI(model_name=OPENAI_MODEL, temperature=0)

    # def create_prompt(self):
    #     return hub.pull("teddynote/rag-korean-with-source")

    def create_prompt(self):
        prompt = ChatPromptTemplate.from_template(
            "당신은 질문-답변(Question-Answering)을 수행하는 친절한 AI 어시스턴트입니다. 당신의 임무는 주어진 문맥(context) 에서 주어진 질문(question) 에 답하는 것입니다.\n"
            "검색된 다음 문맥(context) 을 사용하여 질문(question) 에 답하세요. 만약, 주어진 문맥(context) 에서 답을 찾을 수 없다면, 답을 모른다면 `주어진 정보에서 질문에 대한 정보를 찾을 수 없습니다` 라고 답하세요.\n"
            "기술적인 용어나 이름은 번역하지 않고 그대로 사용해 주세요. 출처(page, source)를 답변에 포함하세요. 답변은 한글로 답변해 주세요.\n"
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

    def create_chain(self, is_docs_input=False):
        self.vectorstore = self.pinecone_load_vectorstore()  # 파인콘 로드

        # 문서 넣으면서 로드
        if is_docs_input == True:
            docs = self.load_documents(self.source_uri)
            text_splitter = self.create_text_splitter()
            split_docs = self.split_documents(docs, text_splitter)
            self.pincone_hybrid_upsert(split_docs)  # 문서 벡터DB에 저장
        self.retriever = self.create_hybrid_retriever()

        model = self.create_model()
        prompt = self.create_prompt()
        self.chain = (
            {"question": itemgetter("question"), "context": itemgetter("context")}
            | prompt
            | model
            | StrOutputParser()
        )
        return self
