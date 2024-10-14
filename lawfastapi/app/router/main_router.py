from fastapi import APIRouter, HTTPException
from schema.graph_state import QueryRequest, QueryResponse
from rag_chain import RAGChain
from dotenv import load_dotenv
import os
import sys

# .env 파일에서 환경변수 불러오기
load_dotenv()

# APIRouter 객체 생성
router = APIRouter()

# 디렉토리 내 모든 파일 경로 가져오기(하위폴더 포함)
def list_files_with_paths(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    rag_chain = RAGChain(list_files_with_paths(sys.argv[1]))
else:
    rag_chain = RAGChain()

@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    result = await rag_chain.process_question(request.query, request.session_id)
    if result:
        return QueryResponse(answer=result["answer"])
    else:
        raise HTTPException(status_code=500, detail="쿼리를 처리하는 데 문제가 발생했습니다.")