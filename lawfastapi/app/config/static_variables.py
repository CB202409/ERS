class StaticVariables:
    # AI모델
    OPENAI_MODEL = "gpt-4o-mini"
    REWRITE_MODEL = "gpt-4o-mini"
    
    # 임베딩 설정
    UPSTAGE_EMBEDDING_MODEL = "solar-embedding-1-large"
    UPSTAGE_RETRIEVE_MODEL = "solar-embedding-1-large-query"
    CHUNK_SIZE = 400
    CHUNK_OVERLAP = 50
    
    # Retrieval
    RETRIEVAL_K = 10
    
    # pinecone
    PINECONE_INDEX_NAME = "law-pdf"
    PINECONE_NAMESPACE = "ns1"
    PDF_DIRECTORY_PATH = "./pdf/"
    SPARSE_ENCODER_PKL_PATH = "./sparse_encoder.pkl"
    
    # 