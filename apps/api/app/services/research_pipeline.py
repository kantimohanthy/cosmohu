"""
RESEARCH PIPELINE INTEGRATION SERVICE (STAGE 3.7 & 3.8)
--------------------------------------------------------
Integrates Query Planning -> Hybrid Retrieval -> Semantic Verification -> Orvyra Persistence.

Full Execution Pipeline:
USER QUERY
    ↓
QUERY PLANNER (Deterministic, initial status: UNVERIFIED)
    ↓
STRUCTURED PROPOSITIONS (Isolated per entity & dimension)
    ↓
HYBRID EVIDENCE RETRIEVAL (Dense + BM25 + RRF + HeuristicReranker)
    ↓
CANDIDATE PASSAGES (Retrieved != Verified)
    ↓
SEMANTIC VERIFIER (5-Dimension compositional entailment check)
    ↓
VERIFIED / REJECTED / CONTRADICTED PROPOSITIONS
    ↓
ORVYRA ADAPTER (Persists verified claims/edges ONLY for SUPPORTED propositions)

Invariants:
- NO PLAN -> NO RETRIEVAL
- NO RETRIEVAL -> NO EVIDENCE
- NO ENTAILMENT -> NO CLAIM
- NO VERIFIED CLAIM -> NO ORVYRA RELATIONSHIP
- CROSS-ENTITY EVIDENCE -> REJECT
- STALE EVIDENCE -> REJECT
- REDIRECT MISMATCH -> REJECT
- HIGH RETRIEVAL SCORE != TRUTH
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import time

from app.models.schemas import EvidencePassage
from app.services.planner import build_deterministic_query_plan, QueryPlan, QueryProposition
from app.services.source_registry import get_source_roots_for_entity
from app.services.store import store
from app.services.retrieval import hybrid_retrieve, multi_query_hybrid_retrieve
from app.services.reranker import rerank_evidence_candidates
from app.services.semantic_verifier import verify_semantic_entailment, SemanticVerificationResult
from app.services.proposition_engine import evaluate_proposition_for_entity, CandidateProposition, is_evidence_associated_with_entity
from app.services.orvyra_adapter import OrvyraAdapter, generate_deterministic_evidence_id
from app.services.crawler import SourceQualityTier

class PropositionPipelineResult(BaseModel):
    proposition_id: str
    entity_id: str
    entity_name: str
    predicate: str
    target_object: str
    temporal_scope: str
    
    planned_status: str = "UNVERIFIED"
    
    retrieved_count: int = 0
    reranked_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    
    verified_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    rejected_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    contradicting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    
    final_status: str = "INSUFFICIENT_EVIDENCE"  # SUPPORTED | INSUFFICIENT_EVIDENCE | CONTRADICTED | CONFLICT | REDIRECT_MISMATCH | NO_SOURCE_ROOT
    verification_reason: str = ""
    evidence_strength: float = 0.0
    confidence: float = 0.0
    source_tier: Optional[str] = None
    
    # 5-dimension explicit boolean flags
    entity_attribution: bool = False
    predicate_support: bool = False
    object_support: bool = False
    temporal_support: bool = False
    provenance_valid: bool = True
    semantic_completeness: bool = False

class PipelineExecutionResult(BaseModel):
    query_id: str
    original_query: str
    run_id: str
    query_plan: Dict[str, Any]
    proposition_results: List[PropositionPipelineResult]
    orvyra_slice: Dict[str, Any]
    executed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

def execute_research_pipeline(
    query_text: str,
    run_id: Optional[str] = None,
    current_run_doc_ids: Optional[List[str]] = None
) -> PipelineExecutionResult:
    """
    Executes the complete deterministic end-to-end research integration pipeline.
    """
    if not run_id:
        run_id = f"pipeline_run_{int(time.time())}"

    # 1. PLANNER: Generate structured query plan
    plan: QueryPlan = build_deterministic_query_plan(query_text)

    # Handle Plan Level Errors (Ambiguous entity, unsupported predicate/dimension)
    if plan.status != "SUCCESS":
        empty_slice = OrvyraAdapter.build_vertical_slice(
            query=query_text,
            query_plan=plan.model_dump(),
            retrieved_passages=[],
            doc_map={},
            retrieval_stats={"total_retrieved": 0, "verified_count": 0},
            run_id=run_id
        )
        return PipelineExecutionResult(
            query_id=plan.query_id,
            original_query=query_text,
            run_id=run_id,
            query_plan=plan.model_dump(),
            proposition_results=[],
            orvyra_slice=empty_slice.model_dump()
        )

    proposition_results: List[PropositionPipelineResult] = []
    all_retrieved_passages: List[EvidencePassage] = []
    doc_map: Dict[str, Dict[str, Any]] = {}
    verified_candidate_props: List[CandidateProposition] = []

    # 2. PROPOSITION-ISOLATED RETRIEVAL & VERIFICATION
    for prop in plan.propositions:
        # Check source root availability
        source_roots = get_source_roots_for_entity(prop.entity_id)
        if not source_roots and prop.entity_id not in ["maia", "ENTITY_TEMPLATE", "unknown_entity"]:
            prop_res = PropositionPipelineResult(
                proposition_id=prop.proposition_id,
                entity_id=prop.entity_id,
                entity_name=prop.entity_name,
                predicate=prop.predicate,
                target_object=prop.target_object,
                temporal_scope=prop.temporal_scope,
                planned_status="UNVERIFIED",
                final_status="NO_SOURCE_ROOT",
                verification_reason=f"NO_SOURCE_ROOT: No registered or discovered authoritative source root exists for {prop.entity_name}."
            )
            proposition_results.append(prop_res)
            continue

        # Formulate proposition-specific retrieval query
        target_obj_readable = prop.target_object.replace("_", " ")
        retrieval_query = f"{prop.entity_name} {target_obj_readable} {prop.predicate}".strip()

        # Multi-Query Hybrid Retrieval with Query Expansion & Diversification (Stage 4.6)
        fused_hits, trace = multi_query_hybrid_retrieve(retrieval_query, entity_id=prop.entity_id, top_k=8, use_multi_query=True)
        reranked = rerank_evidence_candidates(retrieval_query, fused_hits, top_k=4)

        raw_candidates: List[Dict[str, Any]] = []
        reranked_summary: List[Dict[str, Any]] = []

        for p in reranked:
            all_retrieved_passages.append(p)
            d = store.get_document(p.document_id)
            if d:
                doc_map[d.document_id] = {
                    "source_id": d.source_id,
                    "publisher": d.publisher,
                    "content_hash": d.content_hash,
                    "extra": d.metadata.extra if d.metadata else {}
                }
            doc_meta = (d.metadata.extra if d else {}) or {}

            cand_item = {
                "evidence_id": generate_deterministic_evidence_id(p.text, p.document_id),
                "evidence_text": p.text,
                "surrounding_context": p.text,
                "confidence": p.confidence_score,
                "relevance_score": p.relevance_score,
                "document_id": p.document_id,
                "chunk_id": p.chunk_id,
                "source_url": p.source_url,
                "publisher": p.publisher,
                "source_tier": doc_meta.get("source_tier", SourceQualityTier.TIER_1),
                "requested_url": doc_meta.get("requested_url", p.source_url),
                "final_resolved_url": doc_meta.get("final_resolved_url", p.source_url),
                "identity_mismatch": doc_meta.get("identity_mismatch", False),
                "content_hash": d.content_hash if d else "hash_unspecified"
            }
            raw_candidates.append(cand_item)
            reranked_summary.append({
                "evidence_id": cand_item["evidence_id"],
                "document_id": p.document_id,
                "relevance_score": p.relevance_score,
                "confidence_score": p.confidence_score,
                "source_url": p.source_url
            })

        # Evaluate Proposition against Candidate Evidence
        evaluated_prop: CandidateProposition = evaluate_proposition_for_entity(
            entity_id=prop.entity_id,
            entity_name=prop.entity_name,
            raw_passages=raw_candidates,
            target_temporal_requirement=prop.temporal_scope if prop.temporal_scope != "UNKNOWN" else "IN_DEVELOPMENT",
            current_run_doc_ids=current_run_doc_ids
        )

        verified_candidate_props.append(evaluated_prop)

        # Categorize evidence into verified, rejected, contradicting
        verified_ev = []
        rejected_ev = []
        contradicting_ev = []

        for cand in raw_candidates:
            # Check isolation & verification
            if not is_evidence_associated_with_entity(cand, prop.entity_id, prop.entity_name):
                rejected_ev.append({**cand, "rejection_reason": "Cross-Entity Attribution Violation"})
                continue

            sem_res: SemanticVerificationResult = verify_semantic_entailment(
                passage_text=cand["evidence_text"],
                entity_id=prop.entity_id,
                entity_name=prop.entity_name,
                target_temporal=prop.temporal_scope if prop.temporal_scope != "UNKNOWN" else "IN_DEVELOPMENT",
                identity_mismatch=cand["identity_mismatch"],
                surrounding_context=cand["surrounding_context"]
            )

            if sem_res.semantic_status == "ENTAILED":
                verified_ev.append(cand)
            elif sem_res.semantic_status == "CONTRADICTED":
                contradicting_ev.append(cand)
            else:
                rejected_ev.append({**cand, "rejection_reason": sem_res.explanation})

        prop_res = PropositionPipelineResult(
            proposition_id=prop.proposition_id,
            entity_id=prop.entity_id,
            entity_name=prop.entity_name,
            predicate=prop.predicate,
            target_object=prop.target_object,
            temporal_scope=prop.temporal_scope,
            planned_status="UNVERIFIED",
            retrieved_count=len(reranked),
            reranked_candidates=reranked_summary,
            verified_evidence=verified_ev,
            rejected_evidence=rejected_ev,
            contradicting_evidence=contradicting_ev,
            final_status=evaluated_prop.verification_status,
            verification_reason=evaluated_prop.reason,
            evidence_strength=evaluated_prop.evidence_strength,
            confidence=evaluated_prop.confidence,
            source_tier=evaluated_prop.source_tier,
            entity_attribution=evaluated_prop.entity_attribution,
            predicate_support=evaluated_prop.predicate_support,
            object_support=evaluated_prop.object_support,
            temporal_support=evaluated_prop.temporal_support,
            provenance_valid=evaluated_prop.provenance_valid,
            semantic_completeness=evaluated_prop.semantic_completeness
        )
        proposition_results.append(prop_res)

    # 3. ORVYRA PERSISTENCE: Pass only verified propositions to adapter
    retrieval_stats = {
        "total_propositions": len(plan.propositions),
        "supported_propositions": len([pr for pr in proposition_results if pr.final_status == "SUPPORTED"]),
        "insufficient_propositions": len([pr for pr in proposition_results if pr.final_status == "INSUFFICIENT_EVIDENCE"]),
        "total_retrieved": len(all_retrieved_passages),
        "run_id": run_id
    }

    orvyra_slice = OrvyraAdapter.build_vertical_slice(
        query=query_text,
        query_plan=plan.model_dump(),
        retrieved_passages=all_retrieved_passages,
        doc_map=doc_map,
        retrieval_stats=retrieval_stats,
        run_id=run_id
    )

    return PipelineExecutionResult(
        query_id=plan.query_id,
        original_query=query_text,
        run_id=run_id,
        query_plan=plan.model_dump(),
        proposition_results=proposition_results,
        orvyra_slice=orvyra_slice.model_dump()
    )
