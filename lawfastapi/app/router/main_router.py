from fastapi import APIRouter, HTTPException
from schema.graph_state import QueryRequest, QueryResponse
from rag_chain import RAGChain
from dotenv import load_dotenv

# .env 파일에서 환경변수 불러오기
load_dotenv()

# APIRouter 객체 생성
router = APIRouter()

# RAGChain 객체 생성
rag_chain = RAGChain()

@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    result = await rag_chain.process_question(request.query, request.session_id)
    if result:
        return QueryResponse(answer=result["answer"])
    else:
        raise HTTPException(status_code=500, detail="쿼리를 처리하는 데 문제가 발생했습니다.")