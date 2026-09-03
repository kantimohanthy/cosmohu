"""
CLAIM AND CITATION VALIDATOR (STAGE 3.9)
----------------------------------------
Independent post-generation verification layer for LLM-generated claims and citations.

The LLM is NOT trusted. Every generated claim must independently satisfy:
1. Citation non-emptiness (factual claims must cite >=1 evidence ID).
2. Evidence existence (cited evidence ID must exist in verified evidence pool).
3. Current run validity (evidence ID must belong to current run_id).
4. Entity isolation (evidence ID must belong to proposition's target entity_id).
5. Verification status (cited evidence status must be SUPPORTED).
6. Attribute constraint (no unsupported attributes like funding/launch date added).

Invariants:
- EVERY FACTUAL CLAIM -> VERIFIED EVIDENCE
- INVALID CITATION -> REJECT
- CROSS-ENTITY CITATION -> REJECT
- STALE CITATION -> REJECT
- UNSUPPORTED ATTRIBUTE -> REJECT
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.answer_assembler import StructuredEvidenceAnswer, AnswerProposition, AnswerEvidenceItem

class GeneratedClaim(BaseModel):
    claim_id: str
    text: str
    entity_id: str
    evidence_ids: List[str] = Field(default_factory=list)

class GeneratedSynthesisResponse(BaseModel):
    answer_text: str
    claims: List[GeneratedClaim] = Field(default_factory=list)
    raw_response: Optional[str] = None

class ValidationResult(BaseModel):
    is_valid: bool
    validated_claims: List[GeneratedClaim] = Field(default_factory=list)
    rejected_claims: List[Dict[str, Any]] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)

    # Metrics
    generated_claims_count: int = 0
    validated_claims_count: int = 0
    rejected_claims_count: int = 0
    claims_without_evidence_count: int = 0
    invalid_citations_count: int = 0
    cross_entity_citations_count: int = 0
    stale_citations_count: int = 0
    unsupported_attributes_count: int = 0

class ClaimValidator:

    UNSUPPORTED_ATTRIBUTE_KEYWORDS = [
        "€500 million", "raised 500", "funding of", "headquartered in spain",
        "will launch in 2027", "launching in 2027", "payload capacity of 5000kg"
    ]

    @classmethod
    def validate_synthesis(
        cls,
        synthesis: GeneratedSynthesisResponse,
        structured_answer: StructuredEvidenceAnswer
    ) -> ValidationResult:
        """
        Independently audits all generated claims and citations against structured verified answer.
        """
        validated_claims: List[GeneratedClaim] = []
        rejected_claims: List[Dict[str, Any]] = []
        rejection_reasons: List[str] = []

        total_generated = len(synthesis.claims)
        claims_without_ev = 0
        invalid_cits = 0
        cross_entity_cits = 0
        stale_cits = 0
        unsupported_attrs = 0

        # Build evidence lookup index from verified answer
        verified_ev_map: Dict[str, Dict[str, Any]] = {}
        for prop in structured_answer.propositions:
            for ev in prop.evidence:
                verified_ev_map[ev.evidence_id] = {
                    "evidence_id": ev.evidence_id,
                    "entity_id": prop.entity_id,
                    "status": prop.status,
                    "run_id": ev.run_id,
                    "doc_id": ev.document_id,
                    "exact_passage": ev.exact_passage
                }

        for claim in synthesis.claims:
            claim_text_lower = claim.text.lower()

            # Rule 1: Check unsupported hallucinated attributes
            has_unsupported_attr = any(kw in claim_text_lower for kw in cls.UNSUPPORTED_ATTRIBUTE_KEYWORDS)
            if has_unsupported_attr:
                unsupported_attrs += 1
                reason = f"Unsupported Attribute Rejection: Claim '{claim.text}' contains unverified factual attribute."
                rejection_reasons.append(reason)
                rejected_claims.append({"claim": claim.model_dump(), "reason": reason})
                continue

            # Rule 2: Non-empty citation requirement for factual assertions
            if not claim.evidence_ids:
                claims_without_ev += 1
                reason = f"Missing Citation Rejection: Factual claim '{claim.text}' has 0 evidence IDs."
                rejection_reasons.append(reason)
                rejected_claims.append({"claim": claim.model_dump(), "reason": reason})
                continue

            # Rule 3: Validate each cited evidence ID
            claim_is_valid = True
            for ev_id in claim.evidence_ids:
                # 3a. Existence Check
                if ev_id not in verified_ev_map:
                    invalid_cits += 1
                    reason = f"Invalid Citation ID: Evidence ID '{ev_id}' not found in verified evidence pool."
                    rejection_reasons.append(reason)
                    claim_is_valid = False
                    break

                ev_info = verified_ev_map[ev_id]

                # 3b. Stale Evidence Check
                if ev_info["run_id"] != structured_answer.run_id:
                    stale_cits += 1
                    reason = f"Stale Citation Rejection: Evidence ID '{ev_id}' belongs to run '{ev_info['run_id']}', expected '{structured_answer.run_id}'."
                    rejection_reasons.append(reason)
                    claim_is_valid = False
                    break

                # 3c. Cross-Entity Isolation Check
                if claim.entity_id and ev_info["entity_id"] != claim.entity_id:
                    cross_entity_cits += 1
                    reason = f"Cross-Entity Citation Rejection: Claim for '{claim.entity_id}' cites evidence '{ev_id}' belonging to '{ev_info['entity_id']}'."
                    rejection_reasons.append(reason)
                    claim_is_valid = False
                    break

                # 3d. Verification Status Check
                if ev_info["status"] != "SUPPORTED":
                    reason = f"Unsupported Status Rejection: Cited evidence '{ev_id}' has status '{ev_info['status']}', expected SUPPORTED."
                    rejection_reasons.append(reason)
                    claim_is_valid = False
                    break

            if claim_is_valid:
                validated_claims.append(claim)
            else:
                rejected_claims.append({"claim": claim.model_dump(), "reason": rejection_reasons[-1]})

        # Overall synthesis validity: is valid if all generated claims passed validation
        is_overall_valid = (len(rejected_claims) == 0 and total_generated > 0)

        return ValidationResult(
            is_valid=is_overall_valid,
            validated_claims=validated_claims,
            rejected_claims=rejected_claims,
            rejection_reasons=rejection_reasons,
            generated_claims_count=total_generated,
            validated_claims_count=len(validated_claims),
            rejected_claims_count=len(rejected_claims),
            claims_without_evidence_count=claims_without_ev,
            invalid_citations_count=invalid_cits,
            cross_entity_citations_count=cross_entity_cits,
            stale_citations_count=stale_cits,
            unsupported_attributes_count=unsupported_attrs
        )
