from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.services.planner import plan_query_execution
from app.services.retrieval import hybrid_retrieve
from app.services.reranker import rerank_evidence_candidates
from app.services.generator import build_grounded_answer
from app.services.store import store
from app.services.orvyra_adapter import OrvyraAdapter, OrvyraIntegrationResponse
from app.models.schemas import AnswerResponse

router = APIRouter()

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, example="Which European launch companies are developing reusable launch technology?")
    source_filter: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)

@router.post("/query", response_model=AnswerResponse)
def execute_intelligence_query(req: QueryRequest):
    """Executes grounded intelligence query pipeline."""
    try:
        plan = plan_query_execution(req.query)
        fused_hits, stats = hybrid_retrieve(req.query, top_k=20, source_filter=req.source_filter)
        reranked_passages = rerank_evidence_candidates(req.query, fused_hits, top_k=req.top_k)
        
        answer_response = build_grounded_answer(
            query=req.query,
            evidence_passages=reranked_passages,
            query_plan=plan,
            retrieval_stats=stats
        )
        return answer_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/orvyra", response_model=OrvyraIntegrationResponse)
def execute_orvyra_integrated_query(req: QueryRequest):
    """
    Executes Orvyra + CosmoHub Intelligence Engine Vertical Slice Pipeline:
    USER QUERY
    → Query Planner (Intent & Concept Extraction)
    → Dense Retrieval + BM25 Retrieval + RRF Fusion
    → Candidate Reranking
    → Orvyra Evidence Adapter (Maps chunk & document provenance)
    → Statement Claim Extraction & Verification
    → Orvyra Graph Construction & Edge Linking (e.ev non-empty)
    → Conflict Detection & Unsupported Case Handling (Withheld)
    → Grounded Synthesis & Evidence Chain
    """
    try:
        plan = plan_query_execution(req.query)
        fused_hits, stats = hybrid_retrieve(req.query, top_k=20, source_filter=req.source_filter)
        reranked_passages = rerank_evidence_candidates(req.query, fused_hits, top_k=req.top_k)

        # Build document provenance lookup map
        doc_map = {}
        for p in reranked_passages:
            doc = store.get_document(p.document_id)
            if doc:
                doc_map[p.document_id] = {
                    "content_hash": doc.content_hash,
                    "version": doc.version,
                    "publisher": doc.publisher,
                    "source_url": doc.source_url
                }

        orvyra_response = OrvyraAdapter.build_vertical_slice(
            query=req.query,
            query_plan=plan,
            retrieved_passages=reranked_passages,
            doc_map=doc_map,
            retrieval_stats=stats
        )
        return orvyra_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
