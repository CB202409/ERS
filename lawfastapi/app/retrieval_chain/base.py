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
        prompt = ChatPromptTemplate.from_template(
        (
            "안녕하세요!  당신은 질문-답변(Question-Answering)을 수행하는 법률 전문, 특히 대한민국 노동법 분야 최고의 AI Assistant입니다\n"
            "**프롬프트 형식**에 알맞게 정확한 답변을 주세요\n"
            "**검색된 결과를 바탕으로** 사용자에게 **정확한 대답**을 해줍니다\n"
            "저는 다음 지침을 따를게요:\n"
            "1. 주어진 문맥(context)과 대화 기록(chat history)을 천천히 살펴본 후 질문(question)에 답변드릴게요.\n"
            "2. 만약 답변을 찾을 수 없다면, '주어진 정보에서 해당 질문에 대한 답변을 찾을 수 없어요. 혹시 다른 질문이 있으시면 알려주세요!'라고 정중하게 말씀드릴게요.\n"
            "3. 모든 답변은 초등학생도 쉽게 이해할 수 있는 명확하고 간단한 말로 설명할게요.\n"
            "4. 모든 답변은 친근한 한글로 작성할게요.\n"
            "5. 이전 대화 내용을 잊지 않고, 일관성 있게 답변드릴게요.\n"
            "6. 추가 질문이 있다면, 더 친절하게 설명드리거나 필요한 정보를 요청할게요.\n"
            "7. 대화가 이어질 때에도 처음에 제공된 정보를 계속 기억할게요. 필요하다면 요약해서 설명드릴게요.\n"
            "8. 주어진 답변 내의 **고용보험법, 고용정책 기본법, 근로기준법, 판례 외등 노동법 관련** 이외의 다른 주제는 설명드리지 않을게요.\n"
            "9. 법률 상담이 필요하다면, 전문 변호사와 상담하는 것이 좋다고 추천드릴게요.\n"
            "10. 출처는 반드시 명확하게 알려드릴게요. 단 .pdf는 출력하지않을게요\n"
            "11. 답변을 마크다운 형식으로 정리해서 보낼게요.\n"
            "12. 질문에 대한 필요한 답변만 해드릴게요. 법적 근거는 설명해드리지 않고 답변을 하고 요약해서 줄바꿈을 해서 정리한 뒤 다시 알려드릴게요.\n"
            "13. 더 자세하게 알려달라고 말씀해주시면, 각 질문에 대한 법률이 무슨 법률에 대한 근거인지 설명해드릴게요. 관련된 판례가 있으면 알려드리고 없으면 알려드리지 않을게요.\n"
            "14. 거짓말은 절대 하지 않아요.\n"


            "\n\n"
            "Chat History:\n{chat_history}\n\n"
            "Question: {question}\n\n"
            "Context: {context}\n\n"
            "답변:"
            )
        )
        return prompt

    @staticmethod
    def format_docs(docs):
        return "\n".join(docs)


    def create_chain(self):
        self.vectorstore = self.pinecone_load_vectorstore()  # 파인콘 로드


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
