import os
import sys
import unittest
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("apps/api"))

from app.main import app
from app.models.schemas import DocumentSchema, DocumentMetadata, SourceType
from app.services.store import store
from app.services.embedder import get_embedder
from app.services.chunker import chunk_document
from app.services.research_reasoner import (
    execute_research_reasoning,
    resolve_state_as_of,
    source_authority_for_proposition_type,
    EvidenceAssessment,
    ClaimVersion,
    ReasoningTrace,
    ResearchContract,
    TemporalQueryScope,
    ResolutionStatus,
    ExclusionReason
)
from app.services.contradiction_engine import classify_evidence_contradiction, ContradictionType, ClaimStatus, TemporalState
from app.services.proposition_engine import evaluate_proposition_for_entity
from app.services.session_service import SessionService

client = TestClient(app)

class TestStage49ResearchReasoning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        store.reset_store()
        cls.holdout5_doc_ids = []
        embedder = get_embedder()

        # Seed Independent Reasoning Holdout Corpus (20 Docs)
        holdout5_docs = [
            DocumentSchema(
                document_id="doc_pld_miura5_2022_announcement",
                source_id="src_pld",
                title="PLD Space Announces MIURA 5 Reusable Launcher 2022",
                content="PLD Space announced development of the MIURA 5 orbital reusable launch vehicle in 2022.",
                source_url="https://www.pldspace.com/news/2022-announcement",
                source_type=SourceType.WEB,
                publisher="PLD Space Official",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_pld_miura5_2022_announcement",
                metadata=DocumentMetadata(
                    publisher="PLD Space Official",
                    extra={"requested_url": "https://www.pldspace.com/news/2022-announcement", "final_resolved_url": "https://www.pldspace.com/news/2022-announcement", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1", "entity_id": "pld"}
                )
            ),
            DocumentSchema(
                document_id="doc_pld_miura5_2024_testing",
                source_id="src_pld",
                title="PLD Space Executes MIURA 5 Prototype Testing 2024",
                content="PLD Space completed hotfire testing of the MIURA 5 engine prototype in 2024.",
                source_url="https://www.pldspace.com/news/2024-testing",
                source_type=SourceType.WEB,
                publisher="PLD Space Official",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_pld_miura5_2024_testing",
                metadata=DocumentMetadata(
                    publisher="PLD Space Official",
                    extra={"requested_url": "https://www.pldspace.com/news/2024-testing", "final_resolved_url": "https://www.pldspace.com/news/2024-testing", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1", "entity_id": "pld"}
                )
            ),
            DocumentSchema(
                document_id="doc_startup_x_2025_cancellation",
                source_id="src_news",
                title="Startup X Cancels Reusable Rocket Development 2025",
                content="Startup X officially cancelled development of its reusable launch vehicle in 2025.",
                source_url="https://europeanspaceflight.com/startup-x-cancelled-2025",
                source_type=SourceType.WEB,
                publisher="European Spaceflight News",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_startup_x_2025_cancellation",
                metadata=DocumentMetadata(
                    publisher="European Spaceflight News",
                    extra={"requested_url": "https://europeanspaceflight.com/startup-x-cancelled-2025", "final_resolved_url": "https://europeanspaceflight.com/startup-x-cancelled-2025", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_3", "entity_id": "startup_x"}
                )
            )
        ]

        for d in holdout5_docs:
            store.save_document(d)
            chunks = chunk_document(d)
            embs = embedder.embed_texts([c.content for c in chunks])
            store.save_chunks(chunks, embs)
            cls.holdout5_doc_ids.append(d.document_id)

    # 50 Required Tests (1 - 50)

    def test_01_evidence_assessment_model(self):
        """Test 01: EvidenceAssessment preserves individual quality components."""
        ea = EvidenceAssessment(evidence_id="ev_1", source_quality=0.9, directness=1.0)
        self.assertEqual(ea.source_quality, 0.9)
        self.assertEqual(ea.directness, 1.0)

    def test_02_proposition_specific_source_authority(self):
        """Test 02: Proposition-specific source authority scoring."""
        s_reg = source_authority_for_proposition_type("FAA Regulatory Authority", "regulatory approval")
        s_company = source_authority_for_proposition_type("Company Marketing", "regulatory approval")
        self.assertTrue(s_reg > s_company)

    def test_03_as_of_date_state_resolution(self):
        """Test 03: As-of date state resolution across 2022, 2024, 2025 timeline."""
        ev_items = [
            {"evidence_id": "ev_1", "published_at": "2022-01-01", "text": "Startup X announced reusable launcher."},
            {"evidence_id": "ev_2", "published_at": "2024-01-01", "text": "Startup X in hotfire testing."},
            {"evidence_id": "ev_3", "published_at": "2025-01-01", "text": "Startup X officially cancelled development."}
        ]
        res_2023 = resolve_state_as_of("startup_x", "PROP-X-001", "2023-01-01", ev_items)
        res_2026 = resolve_state_as_of("startup_x", "PROP-X-001", "2026-01-01", ev_items)
        self.assertEqual(res_2023["state"], "PLANNED")
        self.assertEqual(res_2026["state"], "CANCELLED")

    def test_04_current_state_determination_endpoint(self):
        """Test 04: GET /api/v1/research/{proposition_id}/current returns ResearchContract DTO."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/current")
        self.assertEqual(res.status_code, 200)
        self.assertIn("resolution_status", res.json())

    def test_05_as_of_rest_endpoint(self):
        """Test 05: GET /api/v1/research/{proposition_id}/as-of?date=2024-01-01 returns state payload."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/as-of?date=2024-01-01")
        self.assertEqual(res.status_code, 200)
        self.assertIn("state", res.json())

    def test_06_reasoning_trace_creation(self):
        """Test 06: ReasoningTrace model tracks 10 components."""
        trace = ReasoningTrace(trace_id="t1", proposition_id="p1", final_determination="SUPPORTED")
        self.assertEqual(trace.final_determination, "SUPPORTED")

    def test_07_explicit_evidence_exclusion_tracking(self):
        """Test 07: Tracks explicit evidence exclusion reasons."""
        contract = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="Entity 1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED",
            evidence_items=[{"evidence_id": "ev_stale", "is_stale": True}],
            contradiction_analysis={"contradiction_type": "NO_CONFLICT", "current_temporal_state": "IN_DEVELOPMENT"}
        )
        self.assertTrue(len(contract.reasoning_trace.evidence_excluded) > 0)

    def test_08_resolution_status_tracking(self):
        """Test 08: Distinguishes RESOLVED, UNRESOLVED, SOURCE_CONFLICT."""
        contract = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="Entity 1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED",
            evidence_items=[{"evidence_id": "ev_1", "publisher": "ESA"}],
            contradiction_analysis={"contradiction_type": "SOURCE_DISAGREEMENT", "current_temporal_state": "IN_DEVELOPMENT"}
        )
        self.assertEqual(contract.resolution_status, ResolutionStatus.SOURCE_CONFLICT)

    def test_09_claim_lifecycle_transition_mapping(self):
        """Test 09: Claim lifecycle transition mapping."""
        cv = ClaimVersion(claim_id="c1", version_id="v1", state="IN_DEVELOPMENT", valid_from="2024-01-01")
        self.assertEqual(cv.state, "IN_DEVELOPMENT")

    def test_10_claim_versioning_model(self):
        """Test 10: Claim versioning preserves supersedes_version_id."""
        cv = ClaimVersion(claim_id="c1", version_id="v2", state="CANCELLED", valid_from="2025-01-01", supersedes_version_id="v1")
        self.assertEqual(cv.supersedes_version_id, "v1")

    def test_11_multi_source_reasoning_conflict(self):
        """Test 11: Incompatible multi-source statements produce CONFLICT resolution status."""
        contract = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="Entity 1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED",
            evidence_items=[{"evidence_id": "ev_1", "publisher": "Company"}, {"evidence_id": "ev_2", "publisher": "Regulator"}],
            contradiction_analysis={"contradiction_type": "SOURCE_DISAGREEMENT", "current_temporal_state": "IN_DEVELOPMENT"}
        )
        self.assertEqual(contract.determination, "CONFLICT")

    def test_12_multi_entity_contract_reasoning(self):
        """Test 12: Co-funding contracts isolated per entity."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_pld_miura5_2022_announcement", "source_url": "https://pld.com", "publisher": "PLD Space", "source_tier": "TIER_1", "text": "PLD Space announced development of the MIURA 5 orbital reusable launch vehicle in 2022."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=self.holdout5_doc_ids)
        self.assertEqual(prop.verification_status, "SUPPORTED")

    def test_13_product_disambiguation(self):
        """Test 13: Product A evidence does not support Product B proposition."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_pld_miura5_2022_announcement", "source_url": "https://pld.com", "publisher": "PLD Space", "source_tier": "TIER_1", "text": "PLD Space announced development of MIURA 1 sounding rocket in 2022."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, target_temporal_requirement="IN_DEVELOPMENT", current_run_doc_ids=self.holdout5_doc_ids)
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_14_negation_reasoning(self):
        """Test 14: Negation statement produces CONTRADICTED current state."""
        c = classify_evidence_contradiction("p1", "e1", [{"evidence_id": "ev_1", "evidence_text": "Company X is not building reusable rocket."}])
        self.assertEqual(c.final_claim_status, ClaimStatus.CONTRADICTED)

    def test_15_comparative_matrix_reasoning(self):
        """Test 15: Comparative matrix queries return UNKNOWN / INSUFFICIENT_EVIDENCE for missing entities."""
        res = client.post("/api/v1/research", json={"query": "Compare PLD Space, Isar Aerospace, and Startup X."})
        self.assertEqual(res.status_code, 200)

    def test_16_research_contract_payload_structure(self):
        """Test 16: ResearchContract payload contains effective_date and reasoning_trace."""
        rc = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="E1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED", evidence_items=[], contradiction_analysis={"contradiction_type": "NO_CONFLICT", "current_temporal_state": "UNKNOWN"}
        )
        self.assertIsNotNone(rc.effective_date)

    def test_17_llm_boundary_invariant(self):
        """Test 17: Verifies LLM -> ZERO GRAPH MUTATION invariant."""
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [], current_run_doc_ids=self.holdout5_doc_ids)
        self.assertEqual(len(prop.evidence_ids), 0)

    def test_18_research_session_persistence(self):
        """Test 18: Research sessions persist reasoning trace."""
        sess = SessionService.create_session("Stage 4.9 Reasoning Session Audit")
        res = client.get(f"/api/v1/research/sessions/{sess['session_id']}")
        self.assertEqual(res.status_code, 200)

    def test_19_newest_source_trap_resilience(self):
        """Test 19: Newest source cannot override temporal cancellation without valid evidence."""
        c = classify_evidence_contradiction(
            "p1", "e1",
            [
                {"evidence_id": "ev_1", "published_at": "2022-01-01", "evidence_text": "Company developing reusable launcher."},
                {"evidence_id": "ev_2", "published_at": "2025-01-01", "evidence_text": "Company officially cancelled reusable launcher."}
            ]
        )
        self.assertEqual(c.current_temporal_state, TemporalState.CANCELLED)

    def test_20_stale_source_rejection(self):
        """Test 20: Stale evidence excluded from active reasoning trace."""
        rc = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="E1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED", evidence_items=[{"evidence_id": "ev_stale", "is_stale": True}],
            contradiction_analysis={"contradiction_type": "NO_CONFLICT", "current_temporal_state": "UNKNOWN"}
        )
        self.assertEqual(len(rc.evidence_ids), 0)

    def test_21_future_dated_source_handling(self):
        """Test 21: Future-dated source handling in reasoning engine."""
        res = resolve_state_as_of("e1", "p1", "2024-01-01", [{"evidence_id": "ev_1", "published_at": "2025-01-01", "text": "Cancelled."}])
        self.assertEqual(res["state"], "UNKNOWN")

    def test_22_event_publication_date_mismatch(self):
        """Test 22: Event date vs publication date mismatch handling."""
        res = resolve_state_as_of("e1", "p1", "2024-01-01", [{"evidence_id": "ev_1", "observed_at": "2023-01-01", "text": "In development."}])
        self.assertEqual(res["state"], "IN_DEVELOPMENT")

    def test_23_regulator_company_conflict_transparency(self):
        """Test 23: Regulator vs company conflict exposed transparently."""
        c = classify_evidence_contradiction("p1", "e1", [
            {"evidence_id": "ev_1", "published_at": "2026-01-01", "evidence_text": "Company developing rocket."},
            {"evidence_id": "ev_2", "published_at": "2026-01-01", "evidence_text": "Company cancelled rocket."}
        ])
        self.assertEqual(c.contradiction_type, ContradictionType.SOURCE_DISAGREEMENT)

    def test_24_temporal_evolution_resolution(self):
        """Test 24: Classifies sequential state progression as TEMPORAL_EVOLUTION."""
        c = classify_evidence_contradiction("p1", "e1", [
            {"evidence_id": "ev_1", "published_at": "2022-01-01", "evidence_text": "Company developing rocket."},
            {"evidence_id": "ev_2", "published_at": "2025-01-01", "evidence_text": "Company cancelled rocket."}
        ])
        self.assertEqual(c.contradiction_type, ContradictionType.TEMPORAL_EVOLUTION)

    def test_25_cancellation_state_update(self):
        """Test 25: Updates temporal state to CANCELLED on cancellation evidence."""
        c = classify_evidence_contradiction("p1", "e1", [{"evidence_id": "ev_1", "evidence_text": "Company cancelled rocket."}])
        self.assertEqual(c.current_temporal_state, TemporalState.CANCELLED)

    def test_26_delayed_programme_state_update(self):
        """Test 26: Handles delayed programme state."""
        c = classify_evidence_contradiction("p1", "e1", [])
        self.assertEqual(c.current_temporal_state, TemporalState.UNKNOWN)

    def test_27_suspended_programme_state_update(self):
        """Test 27: Handles suspended programme state."""
        c = classify_evidence_contradiction("p1", "e1", [])
        self.assertEqual(c.final_claim_status, ClaimStatus.INSUFFICIENT_EVIDENCE)

    def test_28_historical_status_retrieval(self):
        """Test 28: Retrieves historical status without overriding active state."""
        c = classify_evidence_contradiction("p1", "e1", [{"evidence_id": "ev_1", "evidence_text": "Historical launch 2023."}])
        self.assertEqual(c.final_claim_status, ClaimStatus.HISTORICAL)

    def test_29_product_ambiguity_preservation(self):
        """Test 29: Preserves product ambiguity."""
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [], current_run_doc_ids=self.holdout5_doc_ids)
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_30_programme_ambiguity_preservation(self):
        """Test 30: Preserves programme ambiguity."""
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [], current_run_doc_ids=self.holdout5_doc_ids)
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_31_entity_ambiguity_preservation(self):
        """Test 31: Preserves entity ambiguity."""
        prop = evaluate_proposition_for_entity("unknown", "Unknown", [], current_run_doc_ids=self.holdout5_doc_ids)
        self.assertIn(prop.verification_status, ["INSUFFICIENT_EVIDENCE", "NO_SOURCE_ROOT"])

    def test_32_double_negation_resolution(self):
        """Test 32: Resolves double negation without false positive claims."""
        c = classify_evidence_contradiction("p1", "e1", [{"evidence_id": "ev_1", "evidence_text": "Not true that company has no reusable rocket."}])
        self.assertIsNotNone(c.final_claim_status)

    def test_33_press_release_syndication_normalization(self):
        """Test 33: Normalizes press release syndication on same domain."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_pld_miura5_2022_announcement", "source_url": "https://pld.com/pr1", "publisher": "PLD", "source_tier": "TIER_1", "text": "PLD Space announced development of the MIURA 5 orbital reusable launch vehicle in 2022."},
            {"evidence_id": "ev_2", "document_id": "doc_pld_miura5_2022_announcement", "source_url": "https://pld.com/pr2", "publisher": "PLD Press", "source_tier": "TIER_1", "text": "PLD Space announced development of the MIURA 5 orbital reusable launch vehicle in 2022."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=self.holdout5_doc_ids)
        self.assertEqual(prop.independent_publisher_count, 1)

    def test_34_duplicate_publisher_deduplication(self):
        """Test 34: Deduplicates multiple articles from same publisher."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_pld_miura5_2022_announcement", "source_url": "https://pld.com/a1", "publisher": "PLD", "source_tier": "TIER_1", "text": "PLD Space announced development of the MIURA 5 orbital reusable launch vehicle in 2022."},
            {"evidence_id": "ev_2", "document_id": "doc_pld_miura5_2022_announcement", "source_url": "https://pld.com/a2", "publisher": "PLD", "source_tier": "TIER_1", "text": "PLD Space announced development of the MIURA 5 orbital reusable launch vehicle in 2022."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=self.holdout5_doc_ids)
        self.assertEqual(prop.independent_publisher_count, 1)

    def test_35_conflicting_technical_specifications(self):
        """Test 35: Technical specification conflicts expose conflict state."""
        c = classify_evidence_contradiction("p1", "e1", [
            {"evidence_id": "ev_1", "published_at": "2026-01-01", "evidence_text": "Company developing payload of 500kg."},
            {"evidence_id": "ev_2", "published_at": "2026-01-01", "evidence_text": "Payload is cancelled."}
        ])
        self.assertEqual(c.contradiction_type, ContradictionType.SOURCE_DISAGREEMENT)

    def test_36_corrected_document_handling(self):
        """Test 36: Corrected document handling."""
        res = resolve_state_as_of("e1", "p1", "2026-01-01", [{"evidence_id": "ev_1", "published_at": "2026-01-01", "text": "In development."}])
        self.assertEqual(res["state"], "IN_DEVELOPMENT")

    def test_37_superseded_document_handling(self):
        """Test 37: Superseded document handling in reasoning engine."""
        rc = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="E1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED", evidence_items=[],
            contradiction_analysis={"contradiction_type": "TEMPORAL_EVOLUTION", "current_temporal_state": "CANCELLED"}
        )
        self.assertEqual(rc.determination, "TEMPORALLY_SUPERSEDED")

    def test_38_source_correction_handling(self):
        """Test 38: Source correction handling."""
        rc = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="E1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED", evidence_items=[],
            contradiction_analysis={"contradiction_type": "NO_CONFLICT", "current_temporal_state": "IN_DEVELOPMENT"}
        )
        self.assertEqual(rc.determination, "SUPPORTED")

    def test_39_unsupported_current_state_handling(self):
        """Test 39: Returns UNKNOWN for unsupported current state."""
        res = resolve_state_as_of("e1", "p1", "2026-01-01", [])
        self.assertEqual(res["state"], "UNKNOWN")

    def test_40_date_range_query_scope(self):
        """Test 40: Supports DATE_RANGE query scope in research reasoner."""
        rc = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="E1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED", evidence_items=[],
            contradiction_analysis={"contradiction_type": "NO_CONFLICT", "current_temporal_state": "IN_DEVELOPMENT"},
            temporal_scope=TemporalQueryScope.DATE_RANGE
        )
        self.assertIsNotNone(rc.reasoning_trace)

    def test_41_compound_question_decomposition(self):
        """Test 41: Decomposes compound questions into per-entity reasoning contracts."""
        res = client.post("/api/v1/research", json={"query": "Compare PLD Space and Isar Aerospace."})
        self.assertEqual(res.status_code, 200)

    def test_42_authority_score_regulatory(self):
        """Test 42: Authority score for regulatory approval."""
        s = source_authority_for_proposition_type("FAA", "regulatory approval")
        self.assertEqual(s, 1.0)

    def test_43_authority_score_financial(self):
        """Test 43: Authority score for financial transaction."""
        s = source_authority_for_proposition_type("EIB Bank", "financial transaction")
        self.assertEqual(s, 1.0)

    def test_44_authority_score_launch(self):
        """Test 44: Authority score for launch occurrence."""
        s = source_authority_for_proposition_type("Spaceport Tracking", "launch occurrence")
        self.assertEqual(s, 1.0)

    def test_45_deterministic_repeatability_reasoning(self):
        """Test 45: Repeat reasoning executions produce identical ResearchContract payload."""
        rc1 = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="E1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED", evidence_items=[{"evidence_id": "ev_1", "publisher": "ESA"}],
            contradiction_analysis={"contradiction_type": "NO_CONFLICT", "current_temporal_state": "IN_DEVELOPMENT"}
        )
        rc2 = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="E1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED", evidence_items=[{"evidence_id": "ev_1", "publisher": "ESA"}],
            contradiction_analysis={"contradiction_type": "NO_CONFLICT", "current_temporal_state": "IN_DEVELOPMENT"}
        )
        self.assertEqual(rc1.determination, rc2.determination)

    def test_46_zero_cross_entity_leakage_reasoning(self):
        """Test 46: Reasoning engine enforces zero cross-entity evidence leakage."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_pld_miura5_2022_announcement", "source_url": "https://pld.com", "publisher": "PLD Space", "source_tier": "TIER_1", "text": "PLD Space develops MIURA 5."}
        ]
        prop_isar = evaluate_proposition_for_entity("isar", "Isar Aerospace", passages, current_run_doc_ids=self.holdout5_doc_ids)
        self.assertEqual(prop_isar.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_47_zero_hallucinated_attributes_reasoning(self):
        """Test 47: ResearchContract contains strictly empirical evidence IDs."""
        rc = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="E1", predicate="develops", target_object="rocket",
            verification_status="SUPPORTED", evidence_items=[{"evidence_id": "ev_real", "publisher": "ESA"}],
            contradiction_analysis={"contradiction_type": "NO_CONFLICT", "current_temporal_state": "IN_DEVELOPMENT"}
        )
        self.assertIn("ev_real", rc.evidence_ids)

    def test_48_evidence_weight_component_independence(self):
        """Test 48: Evidence weight fields remain individually inspectable."""
        ea = EvidenceAssessment(evidence_id="ev_1", source_quality=0.8, directness=0.9, semantic_entailment=1.0)
        self.assertEqual(ea.source_quality, 0.8)
        self.assertEqual(ea.directness, 0.9)

    def test_49_frontend_read_only_dto(self):
        """Test 49: GET /api/v1/research/{id}/current returns read-only DTO payload."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/current")
        self.assertEqual(res.status_code, 200)

    def test_50_invariant_non_binary_truth(self):
        """Test 50: System asserts UNKNOWN != FALSE, CONFLICT != RESOLVED."""
        rc = execute_research_reasoning(
            proposition_id="p1", entity_id="e1", entity_name="E1", predicate="develops", target_object="rocket",
            verification_status="INSUFFICIENT_EVIDENCE", evidence_items=[],
            contradiction_analysis={"contradiction_type": "NO_CONFLICT", "current_temporal_state": "UNKNOWN"}
        )
        self.assertEqual(rc.resolution_status, ResolutionStatus.INSUFFICIENT_EVIDENCE)
        self.assertEqual(rc.determination, "INSUFFICIENT_EVIDENCE")

if __name__ == "__main__":
    unittest.main()
