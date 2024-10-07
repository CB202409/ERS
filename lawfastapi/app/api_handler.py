from fastapi import APIRouter, HTTPException
from app.models import QueryRequest, QueryResponse
from app.rag_chain import RAGChain
from app.pdf_utils import list_files_with_paths
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

source_list = list_files_with_paths("./pdf/")
rag_chain = RAGChain(source_list)

@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    result = await rag_chain.process_question(request.query, request.session_id)
    if result:
        return QueryResponse(answer=result["answer"])
    else:
        raise HTTPException(status_code=500, detail="쿼리를 처리하는 데 문제가 발생했습니다.")