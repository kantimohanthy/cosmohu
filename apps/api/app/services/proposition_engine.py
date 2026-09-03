"""
PROPOSITION EXTRACTION & VERIFICATION ENGINE (STAGE 3.5.1 HARDENED)
-------------------------------------------------------------------
Evaluates candidate evidence passages against target propositions using the hardened
Compositional 5-Dimension Semantic Verifier Engine.

Invariants:
- NO EVIDENCE -> NO CLAIM
- NO ENTAILED EVIDENCE -> NO CLAIM
- NO VERIFIED CLAIM -> NO ORVYRA RELATIONSHIP
- Only ENTAILED evidence can support a proposition.
- Exposes explicit 5-dimension boolean results.
"""

from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.schemas import EvidencePassage
from app.services.crawler import SourceQualityTier
from app.services.source_registry import source_registry, get_source_roots_for_entity
from app.services.semantic_verifier import verify_semantic_entailment, SemanticVerificationResult

class EvidenceQualityBreakdown(BaseModel):
    retrieval_relevance: float = 0.0
    evidence_strength: float = 0.0
    source_quality: float = 0.0
    semantic_entailment: float = 0.0
    corroboration: float = 0.0
    temporal_validity: float = 0.0
    provenance_validity: float = 1.0
    heuristic_score: float = 0.0
    label: str = "EVIDENCE QUALITY HEURISTIC (NOT TRUTH PROBABILITY)"

class CandidateProposition(BaseModel):
    proposition_id: str
    entity_id: str
    entity_name: str
    predicate: str = "develops"
    target_object: str = "reusable launch vehicle technology"
    expected_statement: str
    verification_status: str = "INSUFFICIENT_EVIDENCE"  # SUPPORTED | INSUFFICIENT_EVIDENCE | REDIRECT_MISMATCH | NO_SOURCE_ROOT | CONFLICT | INVALID_PROVENANCE | CONTRADICTED
    semantic_status: str = "NOT_ENTAILED"  # ENTAILED | PARTIALLY_SUPPORTED | NOT_ENTAILED | CONTRADICTED | INVALID_PROVENANCE
    
    # Explicit 5-Dimension Verification Flags
    entity_attribution: bool = False
    predicate_support: bool = False
    object_support: bool = False
    temporal_support: bool = False
    semantic_completeness: bool = False
    provenance_valid: bool = True
    entailment_type: str = "DIRECT_ENTAILMENT"

    confidence: float = 0.0
    evidence_strength: float = 0.0
    corroboration_count: int = 0
    independent_publisher_count: int = 0
    independent_document_count: int = 0
    corroboration_status: str = "INSUFFICIENT"  # CORROBORATED | SINGLE_SOURCE | INSUFFICIENT
    is_heuristic_confidence: bool = True
    evidence_quality_breakdown: Optional[EvidenceQualityBreakdown] = None
    evidence_ids: List[str] = Field(default_factory=list)
    evidence_id: Optional[str] = None
    evidence_text: Optional[str] = None
    surrounding_context: Optional[str] = None
    document_id: Optional[str] = None
    source_url: Optional[str] = None
    source_tier: Optional[str] = None
    temporal_status: str = "UNSPECIFIED"  # OPERATIONAL | IN_DEVELOPMENT | PLANNED | HISTORICAL | CANCELLED | UNSPECIFIED
    published_at: Optional[str] = None
    observed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    reason: str = ""

def is_evidence_associated_with_entity(ev: Dict[str, Any], entity_id: str, entity_name: str) -> bool:
    """
    Strict Entity Isolation Check:
    Verifies that evidence passage belongs to document/source associated with target entity.
    """
    url = (ev.get("source_url") or ev.get("requested_url") or "").lower()
    publisher = (ev.get("publisher") or "").lower()
    text = (ev.get("evidence_text") or ev.get("text") or "").lower()

    ent_id_lower = entity_id.lower()
    ent_name_lower = entity_name.lower()

    if ent_id_lower in url or ent_name_lower.replace(" ", "") in url:
        return True
    if ent_name_lower in publisher:
        return True
    if ent_name_lower in text or ent_id_lower in text:
        return True

    return False

def evaluate_proposition_for_entity(
    entity_id: str,
    entity_name: str,
    raw_passages: List[Dict[str, Any]],
    target_temporal_requirement: str = "IN_DEVELOPMENT",
    current_run_doc_ids: Optional[List[str]] = None
) -> CandidateProposition:
    """
    Evaluates candidate evidence passages for entity against targeted proposition:
    "[Entity] is developing reusable launch vehicle technology".
    """
    expected_stmt = f"{entity_name} is developing reusable launch vehicle technology."
    prop_id = f"PROP-{entity_id.upper()}-REUSABLE"

    # 1. Audit Source Root
    source_roots = get_source_roots_for_entity(entity_id)
    if not source_roots and entity_id not in ["maia"]:
        return CandidateProposition(
            proposition_id=prop_id,
            entity_id=entity_id,
            entity_name=entity_name,
            expected_statement=expected_stmt,
            verification_status="NO_SOURCE_ROOT",
            semantic_status="NOT_ENTAILED",
            confidence=0.0,
            evidence_strength=0.0,
            corroboration_count=0,
            reason=f"NO_SOURCE_ROOT: No registered or discovered authoritative source root exists for {entity_name}."
        )

    entailed_passages: List[Dict[str, Any]] = []
    contradicted_passages: List[Dict[str, Any]] = []
    mismatch_item: Optional[Dict[str, Any]] = None

    for ev in raw_passages:
        if current_run_doc_ids and ev.get("document_id") not in current_run_doc_ids:
            continue

        # Entity Isolation Filtering: Passage MUST be associated with target entity
        if not is_evidence_associated_with_entity(ev, entity_id, entity_name):
            continue

        text = ev.get("evidence_text") or ev.get("text") or ""
        ctx = ev.get("surrounding_context")
        identity_mismatch = ev.get("identity_mismatch", False)

        sem_res = verify_semantic_entailment(
            passage_text=text,
            entity_id=entity_id,
            entity_name=entity_name,
            target_temporal=target_temporal_requirement,
            identity_mismatch=identity_mismatch,
            surrounding_context=ctx
        )

        ev["semantic_result"] = sem_res

        if sem_res.semantic_status == "INVALID_PROVENANCE":
            mismatch_item = ev
        elif sem_res.semantic_status == "CONTRADICTED":
            contradicted_passages.append(ev)
        elif sem_res.semantic_status == "ENTAILED":
            entailed_passages.append(ev)

    # 2. CONFLICT Detection
    if entailed_passages and contradicted_passages:
        best_e = entailed_passages[0]
        best_c = contradicted_passages[0]
        sem_res: SemanticVerificationResult = best_e["semantic_result"]
        return CandidateProposition(
            proposition_id=prop_id,
            entity_id=entity_id,
            entity_name=entity_name,
            expected_statement=expected_stmt,
            verification_status="CONFLICT",
            semantic_status="CONTRADICTED",
            entity_attribution=sem_res.entity_attribution,
            predicate_support=False,
            object_support=sem_res.object_support,
            temporal_support=False,
            semantic_completeness=False,
            provenance_valid=True,
            confidence=0.50,
            evidence_strength=0.50,
            corroboration_count=len(entailed_passages),
            evidence_id=best_e.get("evidence_id"),
            evidence_text=best_e.get("evidence_text"),
            surrounding_context=best_e.get("surrounding_context"),
            document_id=best_e.get("document_id"),
            source_url=best_e.get("source_url"),
            reason=f"CONFLICT DETECTED: Coexisting supporting evidence ('{best_e.get('source_url')}') and contradicting evidence ('{best_c.get('source_url')}')."
        )

    # 3. CONTRADICTED
    if contradicted_passages and not entailed_passages:
        best_c = contradicted_passages[0]
        sem_res: SemanticVerificationResult = best_c["semantic_result"]
        return CandidateProposition(
            proposition_id=prop_id,
            entity_id=entity_id,
            entity_name=entity_name,
            expected_statement=expected_stmt,
            verification_status="CONTRADICTED",
            semantic_status="CONTRADICTED",
            entity_attribution=sem_res.entity_attribution,
            predicate_support=False,
            object_support=False,
            temporal_support=False,
            semantic_completeness=False,
            provenance_valid=True,
            confidence=0.0,
            evidence_strength=0.0,
            corroboration_count=0,
            evidence_id=best_c.get("evidence_id"),
            evidence_text=best_c.get("evidence_text"),
            surrounding_context=best_c.get("surrounding_context"),
            document_id=best_c.get("document_id"),
            source_url=best_c.get("source_url"),
            reason=f"CONTRADICTED: Passage explicitly refutes reusable launcher development for {entity_name}."
        )

    # 4. SUPPORTED (ENTAILED)
    if entailed_passages:
        best_match = entailed_passages[0]
        ev_ids = [ev.get("evidence_id") for ev in entailed_passages if ev.get("evidence_id")]
        
        unique_urls = set(ev.get("source_url") for ev in entailed_passages if ev.get("source_url"))
        
        # Domain-based publisher normalization (prevents counting different pages from same domain as separate publishers)
        def get_pub_domain(ev_item: Dict[str, Any]) -> str:
            u = (ev_item.get("source_url") or "").lower()
            p = (ev_item.get("publisher") or "").lower()
            if "pldspace.com" in u or "pld space" in p:
                return "pldspace.com"
            if "isaraerospace.com" in u or "isar aerospace" in p:
                return "isaraerospace.com"
            if "rfa.space" in u or "rocket factory" in p:
                return "rfa.space"
            if "orbex.space" in u or "orbex" in p:
                return "orbex.space"
            if "maiaspace.com" in u or "maiaspace" in p:
                return "maiaspace.com"
            if "esa.int" in u or "esa" in p:
                return "esa.int"
            if "eib.org" in u or "eib" in p:
                return "eib.org"
            if u.startswith("http"):
                parts = u.split("//")[-1].split("/")[0].replace("www.", "")
                if parts:
                    return parts
            return p or "unknown_publisher"

        unique_pubs = set(get_pub_domain(ev) for ev in entailed_passages)
        unique_docs = set(ev.get("document_id") for ev in entailed_passages if ev.get("document_id"))
        
        corroboration_count = len(unique_urls)
        indep_pub_count = len(unique_pubs)
        indep_doc_count = len(unique_docs)
        
        corroboration_status = "CORROBORATED" if indep_pub_count >= 2 else ("SINGLE_SOURCE" if indep_pub_count == 1 else "INSUFFICIENT")

        tier = best_match.get("source_tier", SourceQualityTier.TIER_1)
        sem_res: SemanticVerificationResult = best_match["semantic_result"]
        temporal = sem_res.temporal_scope
        raw_conf = best_match.get("confidence", 0.85)

        evidence_strength = round(min(0.95, raw_conf * 0.9), 2)
        heuristic_conf = round(min(0.99, evidence_strength + (0.05 * (corroboration_count - 1))), 2)

        source_qual_val = 1.0 if tier == "TIER_1" else (0.7 if tier == "TIER_2" else (0.5 if tier == "TIER_3" else 0.2))
        sem_ent_val = 1.0 if (sem_res.entity_attribution and sem_res.predicate_support and sem_res.object_support and sem_res.temporal_support and sem_res.semantic_completeness) else 0.0
        corrob_val = 1.0 if corroboration_status == "CORROBORATED" else (0.7 if corroboration_status == "SINGLE_SOURCE" else 0.0)
        temp_val = 1.0 if sem_res.temporal_support else 0.0
        prov_val = 1.0 if sem_res.provenance_valid else 0.0
        
        composite_heuristic = round((0.2 * evidence_strength) + (0.2 * source_qual_val) + (0.3 * sem_ent_val) + (0.15 * corrob_val) + (0.15 * temp_val), 2)
        
        quality_breakdown = EvidenceQualityBreakdown(
            retrieval_relevance=round(raw_conf, 2),
            evidence_strength=evidence_strength,
            source_quality=source_qual_val,
            semantic_entailment=sem_ent_val,
            corroboration=corrob_val,
            temporal_validity=temp_val,
            provenance_validity=prov_val,
            heuristic_score=composite_heuristic,
            label="EVIDENCE QUALITY HEURISTIC (NOT TRUTH PROBABILITY)"
        )

        return CandidateProposition(
            proposition_id=prop_id,
            entity_id=entity_id,
            entity_name=entity_name,
            expected_statement=expected_stmt,
            verification_status="SUPPORTED",
            semantic_status="ENTAILED",
            entity_attribution=sem_res.entity_attribution,
            predicate_support=sem_res.predicate_support,
            object_support=sem_res.object_support,
            temporal_support=sem_res.temporal_support,
            semantic_completeness=sem_res.semantic_completeness,
            provenance_valid=sem_res.provenance_valid,
            entailment_type=sem_res.entailment_type,
            confidence=heuristic_conf,
            evidence_strength=evidence_strength,
            corroboration_count=corroboration_count,
            independent_publisher_count=indep_pub_count,
            independent_document_count=indep_doc_count,
            corroboration_status=corroboration_status,
            is_heuristic_confidence=True,
            evidence_quality_breakdown=quality_breakdown,
            evidence_ids=ev_ids,
            evidence_id=best_match.get("evidence_id"),
            evidence_text=best_match.get("evidence_text") or best_match.get("text"),
            surrounding_context=best_match.get("surrounding_context"),
            document_id=best_match.get("document_id"),
            source_url=best_match.get("source_url"),
            source_tier=tier,
            temporal_status=temporal,
            published_at=best_match.get("published_at"),
            reason=f"Compositional Semantic Entailment Succeeded: Joint ENTITY ({entity_name}) + PREDICATE (development) + OBJECT (reusable launcher) established in {tier} source."
        )

    # 5. REDIRECT_MISMATCH
    if mismatch_item:
        return CandidateProposition(
            proposition_id=prop_id,
            entity_id=entity_id,
            entity_name=entity_name,
            expected_statement=expected_stmt,
            verification_status="REDIRECT_MISMATCH",
            semantic_status="INVALID_PROVENANCE",
            entity_attribution=False,
            predicate_support=False,
            object_support=False,
            temporal_support=False,
            semantic_completeness=False,
            provenance_valid=False,
            confidence=0.0,
            evidence_strength=0.0,
            corroboration_count=0,
            evidence_id=mismatch_item.get("evidence_id"),
            evidence_text=mismatch_item.get("evidence_text") or mismatch_item.get("text"),
            surrounding_context=mismatch_item.get("surrounding_context"),
            document_id=mismatch_item.get("document_id"),
            source_url=mismatch_item.get("source_url"),
            source_tier=mismatch_item.get("source_tier"),
            temporal_status="UNSPECIFIED",
            reason=f"REDIRECT_MISMATCH: Source '{mismatch_item.get('requested_url')}' redirected to '{mismatch_item.get('final_resolved_url')}'. Redirected article rejected as direct evidence for {entity_name}."
        )

    # 6. INSUFFICIENT_EVIDENCE
    return CandidateProposition(
        proposition_id=prop_id,
        entity_id=entity_id,
        entity_name=entity_name,
        expected_statement=expected_stmt,
        verification_status="INSUFFICIENT_EVIDENCE",
        semantic_status="NOT_ENTAILED",
        entity_attribution=False,
        predicate_support=False,
        object_support=False,
        temporal_support=False,
        semantic_completeness=False,
        provenance_valid=True,
        confidence=0.0,
        evidence_strength=0.0,
        corroboration_count=0,
        temporal_status="UNSPECIFIED",
        reason=f"No semantically entailed text passage establishes reusable launcher development for {entity_name}."
    )
