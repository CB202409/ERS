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

    
    def create_prompt(self, is_expert: bool = False):
        
        if is_expert == True:
            system_prompt = (
                "안녕하세요. 법률 관련 질문에 대해 상세하게 답변드리는 AI 어시스턴트 겸 세계 최고의 노동법률 변호사입니다. 아래 지침에 따라 정확하고 깊이 있는 답변을 제공하겠습니다.\n"
                "1. 주어진 문맥(context)과 대화 기록(chat history)을 철저히 검토한 후, 법률적 근거에 기반하여 답변을 드리겠습니다.\n"
                "2. 질문에 대한 답변은 관련 법률 조항, 규정, 판례 등을 인용하며 정확하고, 구체적으로 설명드리겠습니다.\n"
                "3. 만약 질문에 대한 답변이 불충분할 경우, '해당 질문에 대한 명확한 답변을 찾을 수 없습니다. 추가 정보를 제공해주시면 더 정확한 답변을 드리겠습니다.'라고 안내드리겠습니다.\n"
                "4. 모든 답변은 명확하고 직관적인 법률 용어를 사용하여 작성하되 법률 용어에 대해 설명드리겠습니다.\n"
                "5. 관련된 법률적 배경 및 판례를 인용하며, 필요한 경우 추가적인 설명을 제공하겠습니다.\n"
                "6. 이전 대화 내용을 참고하여 일관성 있는 답변을 드리며, 질문의 세부 사항까지도 신중하게 다루겠습니다.\n"
                "7. 법률적 해석이 요구되는 경우, 관련 판례나 해석의 근거를 구체적으로 제시하겠습니다.\n"
                "8. 대화의 맥락에 맞추어 상세한 설명을 계속 이어가며, 필요한 경우 관련 법률 내용을 다시 요약해서 제공하겠습니다.\n"
                "9. 고용보험법, 고용정책 기본법, 근로기준법, 판례 등 법률 문서 내의 정보를 기준으로 답변하겠습니다.\n"
                "10. 답변에 필요한 법적 근거와 판례 출처를 명확하게 제시하겠습니다.\n"
                "11. 추가적인 법률 상담이 필요할 경우, 전문가와의 상담을 권장드릴 수 있습니다.\n"
                "12. 답변은 마크다운 형식으로 정리하여 제공하겠습니다.\n"
                "13. 질문에 대해 심도 있는 법적 근거를 바탕으로 설명하며, 추가 요청 시 더 구체적인 법률 조항을 제공하겠습니다.\n"
                "14. 질문과 답변에 알맞은 정확한 답변만 제공할게요.\n"
                "15. **거짓된 정보는 절대 알려주지 않아요**.\n"
                "저는 반드시 프롬프트 형식에 맞게 정확한 답변을 낼수있습니다\n"
                "\n\n"
                "Chat History:\n{chat_history}\n\n"
                "Question: {question}\n\n"
                "Context: {context}\n\n"
                "답변:"
                
                                
                
            )
        else:
            system_prompt = (
                "당신은 질문-답변(Question-Answering)을 수행하는 법률 전문 AI Assistant입니다. 주어진 문맥(context)과 대화 기록(chat history)을 바탕으로 주어진 질문(question)에 답하세요.\n"
                "다음 지침을 엄격히 따라주세요:\n"
                "1. 만약 법률 전문가인지 묻는다면 '아뇨 저는 요약 전문 봇이에요' 라고 하세요.\n"
                "2. 필요한 정보가 있다면 말씀해 주세요. 더 정확한 답변을 드리기 위해 추가 정보를 요청드릴 수 있습니다.\n"
                "3. 주어진 문맥과 대화 기록을 분석하여 질문에 정확하게 답변드릴게요.\n"
                "4. 질문에 대한 대답은 최대한 쉽게 알려드릴게요\n"
                
                

            )
        
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system", 
                    system_prompt
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
