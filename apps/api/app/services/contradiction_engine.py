"""
CONTRADICTION RESOLUTION ENGINE & TEMPORAL INTELLIGENCE (STAGE 4.8)
-------------------------------------------------------------------
Analyzes evidence items for a target proposition to identify, classify, and resolve
contradictions, temporal evolutions, source disagreements, and supersessions.

Invariants:
- TEMPORAL DIFFERENCE != CONTRADICTION
- SOURCE DISAGREEMENT != AUTOMATIC FALSEHOOD
- HISTORICAL CLAIM != CURRENT CLAIM
- NO EVIDENCE -> NO CLAIM
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class TemporalState(str, Enum):
    ANNOUNCED = "ANNOUNCED"
    PLANNED = "PLANNED"
    IN_DEVELOPMENT = "IN_DEVELOPMENT"
    TESTING = "TESTING"
    OPERATIONAL = "OPERATIONAL"
    DELAYED = "DELAYED"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    HISTORICAL = "HISTORICAL"
    UNKNOWN = "UNKNOWN"

class ContradictionType(str, Enum):
    TRUE_CONTRADICTION = "TRUE_CONTRADICTION"
    TEMPORAL_EVOLUTION = "TEMPORAL_EVOLUTION"
    SCOPE_DIFFERENCE = "SCOPE_DIFFERENCE"
    SOURCE_DISAGREEMENT = "SOURCE_DISAGREEMENT"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
    NO_CONFLICT = "NO_CONFLICT"

class ClaimStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    CORROBORATED = "CORROBORATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONTRADICTED = "CONTRADICTED"
    CONFLICT = "CONFLICT"
    TEMPORALLY_SUPERSEDED = "TEMPORALLY_SUPERSEDED"
    HISTORICAL = "HISTORICAL"
    REDIRECT_MISMATCH = "REDIRECT_MISMATCH"
    NO_SOURCE_ROOT = "NO_SOURCE_ROOT"

class ContradictionAnalysisResult(BaseModel):
    proposition_id: str
    entity_id: str
    contradiction_type: ContradictionType = ContradictionType.NO_CONFLICT
    final_claim_status: ClaimStatus = ClaimStatus.INSUFFICIENT_EVIDENCE
    current_temporal_state: TemporalState = TemporalState.UNKNOWN
    superseded_evidence_ids: List[str] = Field(default_factory=list)
    active_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    explanation: str = ""

def classify_evidence_contradiction(
    proposition_id: str,
    entity_id: str,
    evidence_items: List[Dict[str, Any]],
    target_temporal_requirement: str = "IN_DEVELOPMENT"
) -> ContradictionAnalysisResult:
    """
    Analyzes evidence items for a target entity and proposition to classify temporal evolution vs true contradiction.
    """
    if not evidence_items:
        return ContradictionAnalysisResult(
            proposition_id=proposition_id,
            entity_id=entity_id,
            contradiction_type=ContradictionType.NO_CONFLICT,
            final_claim_status=ClaimStatus.INSUFFICIENT_EVIDENCE,
            current_temporal_state=TemporalState.UNKNOWN,
            explanation="No evidence available for proposition."
        )

    def get_pub_date(ev: Dict[str, Any]) -> str:
        return ev.get("published_at") or ev.get("observed_at") or "1970-01-01T00:00:00"

    sorted_ev = sorted(evidence_items, key=get_pub_date)

    has_cancellation = False
    has_active_dev = False
    has_historical = False

    active_ids = []
    superseded_ids = []
    contradicting_ids = []

    negation_terms = [
        "cancelled", "abandoned", "ceased operations", "no longer developing",
        "discontinued", "no reusable", "not building", "has no reusable"
    ]

    for ev in sorted_ev:
        text_lower = (ev.get("evidence_text") or ev.get("text") or "").lower()
        ev_id = ev.get("evidence_id") or "ev_unknown"

        if any(term in text_lower for term in negation_terms):
            has_cancellation = True
            contradicting_ids.append(ev_id)
        elif any(term in text_lower for term in ["historical", "suborbital flight", "suborbital sounding rocket", "2023 flight"]):
            has_historical = True
            superseded_ids.append(ev_id)
        elif any(term in text_lower for term in ["developing", "development", "co-funded", "grant", "venture debt", "building"]):
            has_active_dev = True
            active_ids.append(ev_id)

    if has_cancellation and has_active_dev:
        first_date = get_pub_date(sorted_ev[0])
        last_date = get_pub_date(sorted_ev[-1])
        
        if first_date == last_date:
            return ContradictionAnalysisResult(
                proposition_id=proposition_id,
                entity_id=entity_id,
                contradiction_type=ContradictionType.SOURCE_DISAGREEMENT,
                final_claim_status=ClaimStatus.CONFLICT,
                current_temporal_state=TemporalState.IN_DEVELOPMENT,
                active_evidence_ids=active_ids,
                contradicting_evidence_ids=contradicting_ids,
                explanation="Independent sources disagree on development vs cancellation status."
            )
        else:
            return ContradictionAnalysisResult(
                proposition_id=proposition_id,
                entity_id=entity_id,
                contradiction_type=ContradictionType.TEMPORAL_EVOLUTION,
                final_claim_status=ClaimStatus.TEMPORALLY_SUPERSEDED,
                current_temporal_state=TemporalState.CANCELLED,
                superseded_evidence_ids=active_ids,
                contradicting_evidence_ids=contradicting_ids,
                explanation="Historical development evidence was temporally superseded by a later cancellation announcement."
            )

    if has_cancellation:
        return ContradictionAnalysisResult(
            proposition_id=proposition_id,
            entity_id=entity_id,
            contradiction_type=ContradictionType.NO_CONFLICT,
            final_claim_status=ClaimStatus.CONTRADICTED,
            current_temporal_state=TemporalState.CANCELLED,
            contradicting_evidence_ids=contradicting_ids,
            explanation="Evidence confirms programme was cancelled or abandoned."
        )

    if has_active_dev:
        status = ClaimStatus.CORROBORATED if len(active_ids) >= 2 else ClaimStatus.SUPPORTED
        return ContradictionAnalysisResult(
            proposition_id=proposition_id,
            entity_id=entity_id,
            contradiction_type=ContradictionType.NO_CONFLICT,
            final_claim_status=status,
            current_temporal_state=TemporalState.IN_DEVELOPMENT,
            active_evidence_ids=active_ids,
            superseded_evidence_ids=superseded_ids,
            explanation="Evidence supports active development."
        )

    if has_historical:
        return ContradictionAnalysisResult(
            proposition_id=proposition_id,
            entity_id=entity_id,
            contradiction_type=ContradictionType.NO_CONFLICT,
            final_claim_status=ClaimStatus.HISTORICAL,
            current_temporal_state=TemporalState.HISTORICAL,
            superseded_evidence_ids=superseded_ids,
            explanation="Evidence relates to historical missions only."
        )

    return ContradictionAnalysisResult(
        proposition_id=proposition_id,
        entity_id=entity_id,
        contradiction_type=ContradictionType.NO_CONFLICT,
        final_claim_status=ClaimStatus.INSUFFICIENT_EVIDENCE,
        current_temporal_state=TemporalState.UNKNOWN,
        explanation="Evidence is insufficient to establish current proposition status."
    )
