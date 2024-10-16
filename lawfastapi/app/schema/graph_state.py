from pydantic import BaseModel
from typing import TypedDict

class GraphState(TypedDict):
    question: str
    context: str
    answer: str
    relevance: str
    session_id: str
    is_expert: bool
    is_rewrite: bool

class QueryRequest(BaseModel):
    query: str
    session_id: str
    is_expert: bool = False

class QueryResponse(BaseModel):
    answer: str
    # context: str
