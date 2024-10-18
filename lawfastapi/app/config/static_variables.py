class StaticVariables:
    # AI모델
    OPENAI_MODEL = "gpt-4o"
    REWRITE_MODEL = "gpt-4o"
    OPENAI_ASSISTANT_CHECKER_MODEL = "gpt-4o"
    OPENAI_ASSISTANT_MODEL = "gpt-4o"
    GROUNDEDNESS_CHECK_MODEL = "gpt-4o"
    
    # 임베딩 설정
    UPSTAGE_EMBEDDING_MODEL = "embedding-passage"
    UPSTAGE_RETRIEVE_MODEL = "embedding-query"
    CHUNK_SIZE = 730
    CHUNK_OVERLAP = 60
    
    # LangSmith 로그 이름
    LANGSMITH_LOG_TITLE="Law-RAG-API"
    
    # Retrieval
    RETRIEVAL_K = 11  # Top-K 문서 반환 개수
    RETRIEVAL_ALPHA = 0.42  # alpha=0.75로 설정한 경우, (0.75: Dense Embedding, 0.25: Sparse Embedding)
    
    # pinecone
    PINECONE_INDEX_NAME = "law-pdf"
    PINECONE_NAMESPACE = "ns1"
    PDF_DIRECTORY_PATH = "./docs/"
    SPARSE_ENCODER_PKL_PATH = "./sparse_encoder.pkl"
    
    # SQLite
    SQLITE_DB_PATH = "./db/chat_history.db"
    
    # OpenAI 어시스턴트용
    OPENAI_ASSISTANT_NAME = "계산"
    OPENAI_ASSISTANT_TEMPERATURE = 0.01
    OPENAI_ASSISTANT_TOP_P = 0.95
    