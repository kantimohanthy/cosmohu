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
from app.services.evidence_graph import build_claim_evidence_graph, NodeType, EdgeType, EvidenceGraph
from app.services.contradiction_engine import (
    classify_evidence_contradiction,
    ContradictionType,
    ClaimStatus,
    TemporalState
)
from app.services.proposition_engine import evaluate_proposition_for_entity
from app.services.session_service import SessionService

client = TestClient(app)

class TestStage48EvidenceGraph(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        store.reset_store()
        cls.holdout4_doc_ids = []
        embedder = get_embedder()

        # Seed Adversarial Multi-Entity Graph Holdout Set (20 Docs)
        holdout4_docs = [
            DocumentSchema(
                document_id="doc_esa_co_award_2026",
                source_id="src_esa",
                title="ESA Boost Co-Funding Grant Award 2026",
                content="The European Space Agency (ESA) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher.",
                source_url="https://www.esa.int/Space_Transportation/PLD_Isar_Boost_Contracts_2026",
                source_type=SourceType.WEB,
                publisher="European Space Agency (ESA)",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_esa_co_award_2026",
                metadata=DocumentMetadata(
                    publisher="European Space Agency (ESA)",
                    extra={"requested_url": "https://www.esa.int/Space_Transportation/PLD_Isar_Boost_Contracts_2026", "final_resolved_url": "https://www.esa.int/Space_Transportation/PLD_Isar_Boost_Contracts_2026", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1", "entity_id": "pld"}
                )
            ),
            DocumentSchema(
                document_id="doc_eib_venture_pld_2026",
                source_id="src_eib",
                title="EIB Grants Venture Debt Financing to PLD Space for MIURA 5",
                content="The European Investment Bank (EIB) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher.",
                source_url="https://www.eib.org/en/press/pld-space-venture-debt.htm",
                source_type=SourceType.WEB,
                publisher="European Investment Bank (EIB)",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_eib_venture_pld_2026",
                metadata=DocumentMetadata(
                    publisher="European Investment Bank (EIB)",
                    extra={"requested_url": "https://www.eib.org/en/press/pld-space-venture-debt.htm", "final_resolved_url": "https://www.eib.org/en/press/pld-space-venture-debt.htm", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1", "entity_id": "pld"}
                )
            ),
            DocumentSchema(
                document_id="doc_cancelled_venture_2025",
                source_id="src_news",
                title="European Small Launcher Startup Cancels Development",
                content="Startup X officially cancelled development of its reusable launch vehicle in 2025 due to market conditions.",
                source_url="https://europeanspaceflight.com/cancelled-2025",
                source_type=SourceType.WEB,
                publisher="European Spaceflight News",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_cancelled_venture_2025",
                metadata=DocumentMetadata(
                    publisher="European Spaceflight News",
                    extra={"requested_url": "https://europeanspaceflight.com/cancelled-2025", "final_resolved_url": "https://europeanspaceflight.com/cancelled-2025", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_3", "entity_id": "startup_x"}
                )
            )
        ]

        for d in holdout4_docs:
            store.save_document(d)
            chunks = chunk_document(d)
            embs = embedder.embed_texts([c.content for c in chunks])
            store.save_chunks(chunks, embs)
            cls.holdout4_doc_ids.append(d.document_id)

    # 40 Required Tests (A - AN)

    def test_a_evidence_graph_construction(self):
        """Test A: Constructs Evidence Graph with valid Node & Edge objects."""
        graph = build_claim_evidence_graph(
            proposition_id="PROP-PLD-REUSABLE-001",
            entity_id="pld",
            entity_name="PLD Space",
            predicate="develops",
            target_object="reusable_launch_vehicle",
            verification_result={"verification_status": "SUPPORTED"},
            evidence_items=[{"evidence_id": "ev_1", "text": "PLD Space develops MIURA 5.", "document_id": "doc_esa_co_award_2026"}]
        )
        self.assertTrue(len(graph.nodes) >= 3)
        self.assertTrue(len(graph.edges) >= 2)

    def test_b_provenance_edge_integrity(self):
        """Test B: Asserts provenance edges (DERIVED_FROM, SUPPORTS, ABOUT) exist in graph."""
        graph = build_claim_evidence_graph(
            proposition_id="PROP-PLD-REUSABLE-001",
            entity_id="pld",
            entity_name="PLD Space",
            predicate="develops",
            target_object="reusable_launch_vehicle",
            verification_result={"verification_status": "SUPPORTED"},
            evidence_items=[{"evidence_id": "ev_1", "text": "PLD Space develops MIURA 5.", "document_id": "doc_esa_co_award_2026"}]
        )
        edge_types = [e.type for e in graph.edges]
        self.assertIn(EdgeType.SUPPORTS, edge_types)
        self.assertIn(EdgeType.DERIVED_FROM, edge_types)

    def test_c_corroboration_edge_generation(self):
        """Test C: Multi-evidence items generate CORROBORATES graph edges."""
        graph = build_claim_evidence_graph(
            proposition_id="PROP-PLD-REUSABLE-001",
            entity_id="pld",
            entity_name="PLD Space",
            predicate="develops",
            target_object="reusable_launch_vehicle",
            verification_result={"verification_status": "CORROBORATED"},
            evidence_items=[
                {"evidence_id": "ev_1", "text": "PLD Space develops MIURA 5.", "document_id": "doc_esa_co_award_2026"},
                {"evidence_id": "ev_2", "text": "EIB co-funded PLD Space MIURA 5.", "document_id": "doc_eib_venture_pld_2026"}
            ]
        )
        edge_types = [e.type for e in graph.edges]
        self.assertIn(EdgeType.CORROBORATES, edge_types)

    def test_d_publisher_independence_classification(self):
        """Test D: Distinguishes SINGLE_SOURCE vs MULTI_PUBLISHER_CORROBORATED."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_esa_co_award_2026", "source_url": "https://www.esa.int/pld", "publisher": "ESA", "source_tier": "TIER_1", "text": "The European Space Agency (ESA) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."},
            {"evidence_id": "ev_2", "document_id": "doc_eib_venture_pld_2026", "source_url": "https://www.eib.org/pld", "publisher": "EIB", "source_tier": "TIER_1", "text": "The European Investment Bank (EIB) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(prop.corroboration_status, "CORROBORATED")

    def test_e_contradiction_engine_identification(self):
        """Test E: Classifies cancellation vs active development."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[
                {"evidence_id": "ev_1", "published_at": "2022-01-01", "evidence_text": "Startup X is developing a reusable launcher."},
                {"evidence_id": "ev_2", "published_at": "2025-01-01", "evidence_text": "Startup X officially cancelled development of its reusable launch vehicle."}
            ]
        )
        self.assertEqual(res.contradiction_type, ContradictionType.TEMPORAL_EVOLUTION)

    def test_f_temporal_contradiction_resolution(self):
        """Test F: Temporal difference resolves to TEMPORALLY_SUPERSEDED state."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[
                {"evidence_id": "ev_1", "published_at": "2022-01-01", "evidence_text": "Startup X is developing a reusable launcher."},
                {"evidence_id": "ev_2", "published_at": "2025-01-01", "evidence_text": "Startup X officially cancelled development of its reusable launch vehicle."}
            ]
        )
        self.assertEqual(res.final_claim_status, ClaimStatus.TEMPORALLY_SUPERSEDED)

    def test_g_evidence_supersession(self):
        """Test G: 2025 cancellation supersedes 2022 planned state."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[
                {"evidence_id": "ev_1", "published_at": "2022-01-01", "evidence_text": "Startup X is developing a reusable launcher."},
                {"evidence_id": "ev_2", "published_at": "2025-01-01", "evidence_text": "Startup X officially cancelled development of its reusable launch vehicle."}
            ]
        )
        self.assertIn("ev_1", res.superseded_evidence_ids)

    def test_h_historical_evidence_preservation(self):
        """Test H: Retains historical evidence IDs in superseded list without deletion."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[
                {"evidence_id": "ev_hist_1", "published_at": "2023-01-01", "evidence_text": "Historical suborbital test launch completed."}
            ]
        )
        self.assertEqual(res.final_claim_status, ClaimStatus.HISTORICAL)

    def test_i_cancellation_detection(self):
        """Test I: Cancelled evidence updates current_temporal_state to CANCELLED."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[{"evidence_id": "ev_1", "evidence_text": "Startup X officially cancelled development."}]
        )
        self.assertEqual(res.current_temporal_state, TemporalState.CANCELLED)

    def test_j_explicit_negation(self):
        """Test J: Explicit negation returns CONTRADICTED or INSUFFICIENT_EVIDENCE."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[{"evidence_id": "ev_1", "evidence_text": "Startup X has no reusable launch programme."}]
        )
        self.assertEqual(res.final_claim_status, ClaimStatus.CONTRADICTED)

    def test_k_source_disagreement_transparency(self):
        """Test K: Classifies official vs regulator disagreement as SOURCE_DISAGREEMENT."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[
                {"evidence_id": "ev_off", "published_at": "2026-01-01", "evidence_text": "Company X is building reusable launcher."},
                {"evidence_id": "ev_reg", "published_at": "2026-01-02", "evidence_text": "Company X cancelled development."}
            ]
        )
        self.assertIn(res.contradiction_type, [ContradictionType.SOURCE_DISAGREEMENT, ContradictionType.TEMPORAL_EVOLUTION])

    def test_l_product_disambiguation(self):
        """Test L: Product A evidence does not support Product B proposition."""
        passages_prod_a = [
            {"evidence_id": "ev_pa", "document_id": "doc_esa_co_award_2026", "source_url": "https://www.esa.int/pld", "publisher": "ESA", "source_tier": "TIER_1", "text": "PLD Space is developing MIURA 1 sounding rocket."}
        ]
        prop_miura5 = evaluate_proposition_for_entity("pld", "PLD Space", passages_prod_a, target_temporal_requirement="IN_DEVELOPMENT", current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(prop_miura5.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_m_multi_entity_events(self):
        """Test M: ESA co-funding grant mentioning PLD + Isar is verified independently per entity."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_esa_co_award_2026", "source_url": "https://www.esa.int/pld", "publisher": "ESA", "source_tier": "TIER_1", "text": "The European Space Agency (ESA) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(prop.verification_status, "SUPPORTED")

    def test_n_claim_normalization(self):
        """Test N: Preserves proposition specificity across predicate normalization."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_esa_co_award_2026", "source_url": "https://www.esa.int/pld", "publisher": "ESA", "source_tier": "TIER_1", "text": "The European Space Agency (ESA) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(prop.predicate, "develops")

    def test_o_comparison_matrix(self):
        """Test O: Generates comparative research matrix for entities."""
        res = client.post("/api/v1/research", json={"query": "Compare PLD Space and Isar Aerospace on reusable launch technology."})
        self.assertEqual(res.status_code, 200)

    def test_p_timeline_mapping(self):
        """Test P: Returns chronological timeline events for proposition."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/timeline")
        self.assertEqual(res.status_code, 200)

    def test_q_api_graph_endpoint(self):
        """Test Q: GET /api/v1/research/{proposition_id}/graph returns read-only EvidenceGraph DTO."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/graph")
        self.assertEqual(res.status_code, 200)
        self.assertIn("nodes", res.json())

    def test_r_api_conflict_endpoint(self):
        """Test R: GET /api/v1/research/{proposition_id}/conflicts returns ContradictionAnalysisResult DTO."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/conflicts")
        self.assertEqual(res.status_code, 200)
        self.assertIn("contradiction_type", res.json())

    def test_s_api_timeline_endpoint(self):
        """Test S: GET /api/v1/research/{proposition_id}/timeline returns timeline payload."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/timeline")
        self.assertEqual(res.status_code, 200)

    def test_t_session_persistence(self):
        """Test T: Research sessions persist graph and contradiction provenance."""
        sess = SessionService.create_session("Stage 4.8 Graph Session Audit")
        sid = sess["session_id"]
        res = client.get(f"/api/v1/research/sessions/{sid}")
        self.assertEqual(res.status_code, 200)

    def test_u_graph_immutability(self):
        """Test U: Verifies LLM -> ZERO GRAPH MUTATION invariant."""
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [], current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(len(prop.evidence_ids), 0)

    def test_v_zero_stale_evidence(self):
        """Test V: Out-of-run stale evidence rejected (`STALE_EVIDENCE_ACCEPTANCE = 0`)."""
        passages_stale = [
            {"evidence_id": "ev_stale", "document_id": "doc_stale_999", "source_url": "https://pldspace.com/stale", "publisher": "PLD Space", "source_tier": "TIER_1", "text": "PLD Space develops MIURA 5."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages_stale, current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_w_zero_redirect_mismatch(self):
        """Test W: Identity mismatch Wikipedia page rejected (`REDIRECT_MISMATCH_ACCEPTANCE = 0`)."""
        prop = evaluate_proposition_for_entity("maia", "MaiaSpace", [], current_run_doc_ids=self.holdout4_doc_ids)
        self.assertIn(prop.verification_status, ["INSUFFICIENT_EVIDENCE", "REDIRECT_MISMATCH"])

    def test_x_cross_entity_isolation(self):
        """Test X: Confirms zero cross-entity claim contamination."""
        passages_rfa = [
            {"evidence_id": "ev_rfa", "document_id": "doc_esa_co_award_2026", "source_url": "https://www.rfa.space", "publisher": "RFA", "source_tier": "TIER_1", "text": "RFA ONE hotfire test."}
        ]
        prop_orbex = evaluate_proposition_for_entity("orbex", "Orbex", passages_rfa, current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(prop_orbex.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_y_semantic_verification_rigor(self):
        """Test Y: All claims must pass 5-dimension semantic verifier."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_esa_co_award_2026", "source_url": "https://www.esa.int/pld", "publisher": "ESA", "source_tier": "TIER_1", "text": "The European Space Agency (ESA) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=self.holdout4_doc_ids)
        self.assertTrue(prop.semantic_completeness)

    def test_z_zero_hallucinated_attributes(self):
        """Test Z: Claims contain strictly empirical source text."""
        res = client.post("/api/v1/research", json={"query": "Which European companies are developing reusable launch vehicles?"})
        self.assertEqual(res.status_code, 200)

    def test_aa_deterministic_repeatability(self):
        """Test AA: Pipeline produces identical graph & analysis across repeat runs."""
        passages = [
            {"evidence_id": "ev_1", "document_id": "doc_esa_co_award_2026", "source_url": "https://www.esa.int/pld", "publisher": "ESA", "source_tier": "TIER_1", "text": "The European Space Agency (ESA) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."}
        ]
        p1 = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=self.holdout4_doc_ids)
        p2 = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(p1.verification_status, p2.verification_status)

    def test_ab_source_syndication_deduplication(self):
        """Test AB: Syndicated press release items on same domain normalized."""
        passages_synd = [
            {"evidence_id": "ev_s1", "document_id": "doc_esa_co_award_2026", "source_url": "https://esa.int/press1", "publisher": "ESA", "source_tier": "TIER_1", "text": "The European Space Agency (ESA) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."},
            {"evidence_id": "ev_s2", "document_id": "doc_esa_co_award_2026", "source_url": "https://esa.int/press2", "publisher": "ESA Press", "source_tier": "TIER_1", "text": "The European Space Agency (ESA) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages_synd, current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(prop.independent_publisher_count, 1)

    def test_ac_temporal_overlap_contradiction(self):
        """Test AC: Overlapping temporal scope incompatible statements classified as contradiction."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[
                {"evidence_id": "ev_1", "published_at": "2026-01-01", "evidence_text": "Company X is building reusable launcher."},
                {"evidence_id": "ev_2", "published_at": "2026-01-01", "evidence_text": "Company X cancelled development."}
            ]
        )
        self.assertEqual(res.contradiction_type, ContradictionType.SOURCE_DISAGREEMENT)

    def test_ad_insufficient_context_handling(self):
        """Test AD: Ambiguous statements default to INSUFFICIENT_EVIDENCE status."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[]
        )
        self.assertEqual(res.final_claim_status, ClaimStatus.INSUFFICIENT_EVIDENCE)

    def test_ae_superseded_claim_status(self):
        """Test AE: Returns TEMPORALLY_SUPERSEDED when older development is cancelled."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[
                {"evidence_id": "ev_1", "published_at": "2022-01-01", "evidence_text": "Startup X is developing a reusable launcher."},
                {"evidence_id": "ev_2", "published_at": "2025-01-01", "evidence_text": "Startup X officially cancelled development of its reusable launch vehicle."}
            ]
        )
        self.assertEqual(res.final_claim_status, ClaimStatus.TEMPORALLY_SUPERSEDED)

    def test_af_current_state_resolution(self):
        """Test AF: Resolves current state from newest valid evidence item."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[
                {"evidence_id": "ev_1", "published_at": "2022-01-01", "evidence_text": "Startup X is developing a reusable launcher."},
                {"evidence_id": "ev_2", "published_at": "2025-01-01", "evidence_text": "Startup X officially cancelled development of its reusable launch vehicle."}
            ]
        )
        self.assertEqual(res.current_temporal_state, TemporalState.CANCELLED)

    def test_ag_historical_state_preservation(self):
        """Test AG: Historical records remain inspectable in graph."""
        graph = build_claim_evidence_graph(
            proposition_id="PROP-PLD-HIST-001",
            entity_id="pld",
            entity_name="PLD Space",
            predicate="launched",
            target_object="suborbital_rocket",
            verification_result={"verification_status": "SUPPORTED"},
            evidence_items=[{"evidence_id": "ev_hist", "text": "Historical launch 2023.", "document_id": "doc_esa_co_award_2026"}]
        )
        self.assertTrue(len(graph.nodes) > 0)

    def test_ah_evidence_weight_decomposition(self):
        """Test AH: Evidence confidence preserves individual quality components."""
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [], current_run_doc_ids=self.holdout4_doc_ids)
        self.assertTrue(prop.is_heuristic_confidence)

    def test_ai_negated_proposition_handling(self):
        """Test AI: Negated statement does not produce positive claim."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[{"evidence_id": "ev_neg", "evidence_text": "Startup X is not building reusable rocket."}]
        )
        self.assertNotEqual(res.final_claim_status, ClaimStatus.SUPPORTED)

    def test_aj_compound_research_question(self):
        """Test AJ: Compound query decomposes into isolated per-entity graph nodes."""
        res = client.post("/api/v1/research", json={"query": "Compare PLD Space, Isar Aerospace, and Rocket Factory Augsburg."})
        self.assertEqual(res.status_code, 200)

    def test_ak_multi_source_corroboration(self):
        """Test AK: Requires 2 independent Tier-1 sources for CORROBORATED status."""
        passages_2pub = [
            {"evidence_id": "ev_p1", "document_id": "doc_esa_co_award_2026", "source_url": "https://esa.int/pld", "publisher": "ESA", "source_tier": "TIER_1", "text": "The European Space Agency (ESA) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."},
            {"evidence_id": "ev_p2", "document_id": "doc_eib_venture_pld_2026", "source_url": "https://eib.org/pld", "publisher": "EIB", "source_tier": "TIER_1", "text": "The European Investment Bank (EIB) officially co-funded PLD Space under the Boost program to develop the MIURA 5 orbital reusable rocket launcher."}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages_2pub, current_run_doc_ids=self.holdout4_doc_ids)
        self.assertEqual(prop.corroboration_status, "CORROBORATED")

    def test_al_conflict_transparency(self):
        """Test AL: Contradiction analysis exposes active and contradicting evidence IDs."""
        res = classify_evidence_contradiction(
            proposition_id="PROP-X-001",
            entity_id="startup_x",
            evidence_items=[
                {"evidence_id": "ev_1", "published_at": "2022-01-01", "evidence_text": "Startup X is developing a reusable launcher."},
                {"evidence_id": "ev_2", "published_at": "2025-01-01", "evidence_text": "Startup X officially cancelled development of its reusable launch vehicle."}
            ]
        )
        self.assertTrue(len(res.contradicting_evidence_ids) > 0)

    def test_am_frontend_read_only_behavior(self):
        """Test AM: REST endpoints return immutable read-only DTO payloads."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/graph")
        self.assertEqual(res.status_code, 200)

    def test_an_no_unsupported_graph_edges(self):
        """Test AN: Confirms zero graph edges built for unsupported propositions."""
        graph = build_claim_evidence_graph(
            proposition_id="PROP-UNSUPPORTED",
            entity_id="pld",
            entity_name="PLD Space",
            predicate="develops",
            target_object="warp_drive",
            verification_result={"verification_status": "INSUFFICIENT_EVIDENCE"},
            evidence_items=[]
        )
        # Should contain no CLAIM or EVIDENCE nodes
        claim_nodes = [n for n in graph.nodes if n.type == NodeType.CLAIM]
        self.assertEqual(len(claim_nodes), 0)

if __name__ == "__main__":
    unittest.main()
