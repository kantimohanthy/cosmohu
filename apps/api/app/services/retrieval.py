"""
MULTI-QUERY HYBRID RETRIEVAL & EVIDENCE ACQUISITION ENGINE (STAGE 4.7)
-----------------------------------------------------------------------
Executes multi-query dense + sparse (BM25) fusion via Reciprocal Rank Fusion (RRF),
document-level diversification, evidence-first retry passes, and structured retrieval tracing.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from app.models.schemas import ChunkSchema, EvidencePassage
from app.services.embedder import get_embedder
from app.services.store import store
from app.services.query_expander import generate_expanded_queries
from app.config import settings

class RetrievalTrace(BaseModel):
    original_query: str
    target_entity_id: Optional[str] = None
    expanded_queries: List[str] = Field(default_factory=list)
    retrieval_methods: List[str] = Field(default_factory=lambda: ["DENSE_COSINE", "SPARSE_BM25", "MULTI_QUERY_RRF", "DOCUMENT_DIVERSIFICATION"])
    dense_results_count: int = 0
    sparse_results_count: int = 0
    fused_results_count: int = 0
    document_diversity_count: int = 0
    retrieval_attempts: int = 1
    retry_performed: bool = False
    rejected_candidates_count: int = 0
    rejection_reasons: List[str] = Field(default_factory=list)
    execution_ms: float = 0.0

def reciprocal_rank_fusion(
    dense_results: List[Tuple[ChunkSchema, float]],
    sparse_results: List[Tuple[ChunkSchema, float]],
    rrf_k: int = 60,
    top_k: int = settings.RETRIEVAL_TOP_K
) -> List[Tuple[ChunkSchema, float]]:
    """
    Fuses dense vector results and sparse keyword search results using
    Reciprocal Rank Fusion (RRF): score = sum(1 / (rrf_k + rank)).
    """
    rrf_scores: Dict[str, float] = {}
    chunk_map: Dict[str, ChunkSchema] = {}

    for rank, (chk, _) in enumerate(dense_results, 1):
        chk_id = chk.chunk_id
        chunk_map[chk_id] = chk
        rrf_scores[chk_id] = rrf_scores.get(chk_id, 0.0) + (1.0 / (rrf_k + rank))

    for rank, (chk, _) in enumerate(sparse_results, 1):
        chk_id = chk.chunk_id
        chunk_map[chk_id] = chk
        rrf_scores[chk_id] = rrf_scores.get(chk_id, 0.0) + (1.0 / (rrf_k + rank))

    sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [(chunk_map[chk_id], score) for chk_id, score in sorted_chunks[:top_k]]

def apply_document_diversification(
    candidates: List[Tuple[ChunkSchema, float]],
    max_chunks_per_doc: int = 3,
    top_k: int = settings.RETRIEVAL_TOP_K
) -> List[Tuple[ChunkSchema, float]]:
    """
    Applies document-level diversification to prevent returning 10 chunks from
    the same document when distinct independent documents exist.
    """
    doc_counts: Dict[str, int] = {}
    diversified: List[Tuple[ChunkSchema, float]] = []

    for chk, score in candidates:
        doc_id = chk.document_id
        current_count = doc_counts.get(doc_id, 0)
        if current_count < max_chunks_per_doc:
            doc_counts[doc_id] = current_count + 1
            diversified.append((chk, score))
            if len(diversified) >= top_k:
                break

    return diversified

def multi_query_hybrid_retrieve(
    query_text: str,
    entity_id: Optional[str] = None,
    top_k: int = settings.RETRIEVAL_TOP_K,
    source_filter: Optional[str] = None,
    use_multi_query: bool = True
) -> Tuple[List[Tuple[ChunkSchema, float]], RetrievalTrace]:
    """
    Executes Multi-Query Hybrid Retrieval with Controlled Evidence Retry:
    1. Deterministic Query Expansion (3-4 query formulations)
    2. Attempt 1: Dense + Sparse BM25 retrieval across expanded queries
    3. Attempt 2 (Retry): If Attempt 1 produces 0 candidates, fallback to entity broad terms
    4. Multi-list RRF fusion & document-level diversification
    5. Structured RetrievalTrace creation
    """
    t0 = time.time()
    embedder = get_embedder()

    expanded_queries = generate_expanded_queries(query_text, entity_id=entity_id) if use_multi_query else [query_text]

    all_dense: List[Tuple[ChunkSchema, float]] = []
    all_sparse: List[Tuple[ChunkSchema, float]] = []
    retrieval_attempts = 1
    retry_performed = False

    for eq in expanded_queries:
        q_emb = embedder.embed_query(eq)
        d_hits = store.search_vector_dense(q_emb, top_k=top_k, source_filter=source_filter)
        s_hits = store.search_keyword_sparse(eq, top_k=top_k, source_filter=source_filter)
        all_dense.extend(d_hits)
        all_sparse.extend(s_hits)

    fused = reciprocal_rank_fusion(all_dense, all_sparse, top_k=top_k * 2)

    # Controlled Evidence-First Retry Pass if Attempt 1 produced 0 fused candidates
    if not fused and entity_id:
        retrieval_attempts = 2
        retry_performed = True
        retry_query = f"{entity_id} orbital launch vehicle rocket"
        q_emb_retry = embedder.embed_query(retry_query)
        d_hits_retry = store.search_vector_dense(q_emb_retry, top_k=top_k, source_filter=source_filter)
        s_hits_retry = store.search_keyword_sparse(retry_query, top_k=top_k, source_filter=source_filter)
        all_dense.extend(d_hits_retry)
        all_sparse.extend(s_hits_retry)
        fused = reciprocal_rank_fusion(all_dense, all_sparse, top_k=top_k * 2)

    diversified = apply_document_diversification(fused, max_chunks_per_doc=3, top_k=top_k)

    unique_docs = set(chk.document_id for chk, _ in diversified)
    exec_ms = round((time.time() - t0) * 1000, 2)

    trace = RetrievalTrace(
        original_query=query_text,
        target_entity_id=entity_id,
        expanded_queries=expanded_queries,
        retrieval_methods=["DENSE_COSINE", "SPARSE_BM25", "MULTI_QUERY_RRF", "DOCUMENT_DIVERSIFICATION"],
        dense_results_count=len(all_dense),
        sparse_results_count=len(all_sparse),
        fused_results_count=len(fused),
        document_diversity_count=len(unique_docs),
        retrieval_attempts=retrieval_attempts,
        retry_performed=retry_performed,
        execution_ms=exec_ms
    )

    return diversified, trace

def hybrid_retrieve(
    query_text: str,
    top_k: int = settings.RETRIEVAL_TOP_K,
    source_filter: Optional[str] = None
) -> Tuple[List[Tuple[ChunkSchema, float]], Dict[str, int]]:
    """Legacy backward-compatible wrapper."""
    candidates, trace = multi_query_hybrid_retrieve(query_text, top_k=top_k, source_filter=source_filter, use_multi_query=False)
    stats = {
        "dense_results": trace.dense_results_count,
        "keyword_results": trace.sparse_results_count,
        "fused_results": trace.fused_results_count
    }
    return candidates, stats
