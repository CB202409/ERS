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
from config.static_variables import StaticVariables

import os


class RetrievalChain(ABC):
    def __init__(self):
        self.source_uri = None

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

    def pincone_hybrid_upsert(self, split_docs, namespace):
        # 파인콘 인덱스 로드
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        pc_index = pc.Index(StaticVariables.PINECONE_INDEX_NAME)

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
            namespace=namespace,
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
                (
                    "당신은 질문-답변(Question-Answering)을 수행하는 법률 전문, 특히 노동법 분야 최고의 AI Assistant입니다. "
                    "주어진 문맥(context)과 대화 기록(chat history)을 바탕으로 주어진 질문(question)에 답하세요. "
                    "또한, 자료의 출처를 최대한 자세하게 밝혀주세요."
                )
            ),
            (
                "system", 
                "다음 지침을 엄격히 따라주세요:"
            ),
            (
                "system", 
                "1. 검색된 문맥(context)과 대화 기록(chat history)을 신중히 분석하여 질문(question)에 답하세요."
            ),
            (
                "system", 
                "2. 만약 비슷한 판례가 있는지를 물어볼 경우 해당 판례를 찾아서 간략하게 알려주세요."
            ),
            (
                "system", 
                "또한, 사용자의 질문이 불명확할 경우, 구체적인 정보를 요청하여 대화를 이어가세요"
            ),
            (
                "system",
                "현재 프롬프트에 형식에 맞게 답변을 내줘"
            ),
            (
                "system",
                "대답은 json형식으로 해줘 예를들면 다음과 같아"
            ),
            (
                "system",
                "대답: 사용자 질문에 관한 대답"                
            ),
            (
                "system",
                "질문과 유사한 판례 or 법률 정보 : 해당 법률이나 판례의 관한 대답"

            ),

                ("system", "Chat History:\n{chat_history}"),
                ("system", "Context:\n{context}"),
                ("human", "Question: {question}\n\n")
            ]
        )
        return prompt

    @staticmethod
    def format_docs(docs):
        return "\n".join(docs)

    def write_pinecone_with_docs(self, source_uri, namespace):
        docs = self.load_documents(source_uri)
        text_splitter = self.create_text_splitter()
        split_docs = self.split_documents(docs, text_splitter)
        self.pincone_hybrid_upsert(split_docs,namespace)  # 문서 벡터DB에 저장

    def create_chain(self, is_docs_input=False):
        self.vectorstore = self.pinecone_load_vectorstore()  # 파인콘 로드

        # 파인콘에 문서 업로드
        if is_docs_input == True:
            self.write_pinecone_with_docs(self.source_uri, StaticVariables.PINECONE_NAMESPACE)

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