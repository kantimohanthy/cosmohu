from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from app.services.retrieval import hybrid_retrieve
from app.services.reranker import rerank_evidence_candidates
from app.models.schemas import EvidencePassage

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    source_filter: Optional[str] = None
    top_k: int = 10

class SearchResponse(BaseModel):
    query: str
    results: List[EvidencePassage]
    total_hits: int

@router.post("/search", response_model=SearchResponse)
def execute_knowledge_search(req: SearchRequest):
    fused_hits, stats = hybrid_retrieve(req.query, top_k=20, source_filter=req.source_filter)
    passages = rerank_evidence_candidates(req.query, fused_hits, top_k=req.top_k)
    return SearchResponse(
        query=req.query,
        results=passages,
        total_hits=len(passages)
    )
