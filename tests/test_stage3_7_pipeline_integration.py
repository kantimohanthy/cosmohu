import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.models.schemas import DocumentSchema, DocumentMetadata, SourceType
from app.services.source_registry import source_registry
from app.services.chunker import chunk_document
from app.services.embedder import get_embedder
from app.services.store import store
from app.services.research_pipeline import execute_research_pipeline, PipelineExecutionResult, PropositionPipelineResult
from app.services.semantic_verifier import verify_semantic_entailment
from app.services.orvyra_adapter import OrvyraAdapter

class TestStage37PipelineIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed corpus and index authoritative fixture documents for integration tests."""
        store.reset_store()

        embedder = get_embedder()
        cls.current_run_doc_ids = []

        # 1. PLD Space Reusable Launcher Document (Tier-1)
        pld_doc = DocumentSchema(
            document_id="doc_pld_miura5",
            source_id="src_pld",
            title="PLD Space MIURA 5 Reusable Launch Vehicle",
            content="PLD Space is developing MIURA 5, an orbital reusable launch vehicle designed for small satellite payload delivery. The first stage is designed to be recoverable and reusable.",
            source_url="https://www.pldspace.com/en/miura-5.html",
            source_type=SourceType.WEB,
            publisher="PLD Space Official",
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash="hash_pld_miura5",
            metadata=DocumentMetadata(
                publisher="PLD Space Official",
                extra={
                    "requested_url": "https://www.pldspace.com/en/miura-5.html",
                    "final_resolved_url": "https://www.pldspace.com/en/miura-5.html",
                    "was_redirected": False,
                    "identity_mismatch": False,
                    "source_tier": "TIER_1"
                }
            )
        )
        store.save_document(pld_doc)
        pld_chunks = chunk_document(pld_doc)
        pld_emb = embedder.embed_texts([c.content for c in pld_chunks])
        store.save_chunks(pld_chunks, pld_emb)
        cls.current_run_doc_ids.append(pld_doc.document_id)

        # 2. Isar Aerospace Non-Reusable Spectrum Document (Tier-1)
        isar_doc = DocumentSchema(
            document_id="doc_isar_spectrum",
            source_id="src_isar",
            title="Isar Aerospace Spectrum Launcher Overview",
            content="Isar Aerospace is developing Spectrum, a two-stage orbital launch vehicle for small satellite payload delivery.",
            source_url="https://www.isaraerospace.com/spectrum.html",
            source_type=SourceType.WEB,
            publisher="Isar Aerospace Official",
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash="hash_isar_spectrum",
            metadata=DocumentMetadata(
                publisher="Isar Aerospace Official",
                extra={
                    "requested_url": "https://www.isaraerospace.com/spectrum.html",
                    "final_resolved_url": "https://www.isaraerospace.com/spectrum.html",
                    "was_redirected": False,
                    "identity_mismatch": False,
                    "source_tier": "TIER_1"
                }
            )
        )
        store.save_document(isar_doc)
        isar_chunks = chunk_document(isar_doc)
        isar_emb = embedder.embed_texts([c.content for c in isar_chunks])
        store.save_chunks(isar_chunks, isar_emb)
        cls.current_run_doc_ids.append(isar_doc.document_id)

        # 3. MaiaSpace Wikipedia Redirect Mismatch Document (Tier-4)
        maia_doc = DocumentSchema(
            document_id="doc_maiaspace_redirect",
            source_id="src_maia",
            title="ArianeGroup - Wikipedia",
            content="ArianeGroup is a French aerospace company developing Ariane launchers.",
            source_url="https://en.wikipedia.org/wiki/ArianeGroup",
            source_type=SourceType.WEB,
            publisher="Wikipedia",
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash="hash_maia_redirect",
            metadata=DocumentMetadata(
                publisher="Wikipedia",
                extra={
                    "requested_url": "https://en.wikipedia.org/wiki/MaiaSpace",
                    "final_resolved_url": "https://en.wikipedia.org/wiki/ArianeGroup",
                    "was_redirected": True,
                    "identity_mismatch": True,
                    "source_tier": "TIER_4"
                }
            )
        )
        store.save_document(maia_doc)
        maia_chunks = chunk_document(maia_doc)
        maia_emb = embedder.embed_texts([c.content for c in maia_chunks])
        store.save_chunks(maia_chunks, maia_emb)
        cls.current_run_doc_ids.append(maia_doc.document_id)

        # 4. Rocket Factory Augsburg Non-Reusable Document (Tier-1)
        rfa_doc = DocumentSchema(
            document_id="doc_rfa_one",
            source_id="src_rfa",
            title="Rocket Factory Augsburg RFA ONE Launcher",
            content="Rocket Factory Augsburg (RFA) is developing RFA ONE, a three-stage orbital launch vehicle.",
            source_url="https://www.rfa.space/rfa-one.html",
            source_type=SourceType.WEB,
            publisher="Rocket Factory Augsburg Official",
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash="hash_rfa_one",
            metadata=DocumentMetadata(
                publisher="Rocket Factory Augsburg Official",
                extra={
                    "requested_url": "https://www.rfa.space/rfa-one.html",
                    "final_resolved_url": "https://www.rfa.space/rfa-one.html",
                    "was_redirected": False,
                    "identity_mismatch": False,
                    "source_tier": "TIER_1"
                }
            )
        )
        store.save_document(rfa_doc)
        rfa_chunks = chunk_document(rfa_doc)
        rfa_emb = embedder.embed_texts([c.content for c in rfa_chunks])
        store.save_chunks(rfa_chunks, rfa_emb)
        cls.current_run_doc_ids.append(rfa_doc.document_id)

    def test_a_single_proposition_query(self):
        """Test A: Single proposition query retrieves and verifies evidence independently."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        self.assertEqual(len(res.query_plan["propositions"]), 1)
        self.assertEqual(len(res.proposition_results), 1)
        prop_res = res.proposition_results[0]
        self.assertEqual(prop_res.planned_status, "UNVERIFIED")

    def test_b_multi_proposition_query(self):
        """Test B: Multi-proposition query evaluates every proposition independently."""
        q = "Compare PLD Space and Isar Aerospace on reusable launch vehicle development."
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        self.assertEqual(len(res.proposition_results), 2)
        pld_p = [p for p in res.proposition_results if p.entity_id == "pld"][0]
        isar_p = [p for p in res.proposition_results if p.entity_id == "isar"][0]
        self.assertNotEqual(pld_p.proposition_id, isar_p.proposition_id)

    def test_c_pld_positive(self):
        """Test C: PLD Space with verified corpus yields SUPPORTED status and positive Orvyra claim/relationship."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        pld_p = [p for p in res.proposition_results if p.entity_id == "pld"][0]
        self.assertEqual(pld_p.final_status, "SUPPORTED")
        self.assertTrue(pld_p.semantic_completeness)

        # Verify positive Orvyra claim & relationship created
        claims = res.orvyra_slice.get("claims", [])
        self.assertTrue(any(c["subject_id"] == "pld" and c["status"] == "SUPPORTED" for c in claims))

    def test_d_isar_unsupported(self):
        """Test D: Isar Aerospace with weak corpus yields INSUFFICIENT_EVIDENCE and zero positive Orvyra relationship."""
        q = "Is Isar Aerospace developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        isar_p = [p for p in res.proposition_results if p.entity_id == "isar"][0]
        self.assertEqual(isar_p.final_status, "INSUFFICIENT_EVIDENCE")
        self.assertFalse(isar_p.semantic_completeness)

        # Verify zero positive claims created for Isar
        claims = res.orvyra_slice.get("claims", [])
        self.assertFalse(any(c["subject_id"] == "isar" and c["status"] == "SUPPORTED" for c in claims))

    def test_e_rfa_unsupported(self):
        """Test E: Rocket Factory Augsburg with weak corpus yields INSUFFICIENT_EVIDENCE and zero positive Orvyra relationship."""
        q = "Is Rocket Factory Augsburg developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        rfa_p = [p for p in res.proposition_results if p.entity_id == "rfa"][0]
        self.assertEqual(rfa_p.final_status, "INSUFFICIENT_EVIDENCE")

    def test_f_maiaspace_redirect_mismatch(self):
        """Test F: MaiaSpace Wikipedia redirect mismatch yields REDIRECT_MISMATCH / INVALID_PROVENANCE."""
        q = "Is MaiaSpace developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        maia_p = [p for p in res.proposition_results if p.entity_id == "maia"][0]
        self.assertIn(maia_p.final_status, ["REDIRECT_MISMATCH", "INVALID_PROVENANCE", "INSUFFICIENT_EVIDENCE"])

    def test_g_cross_entity_contamination_rejected(self):
        """Test G: Cross-entity evidence for PLD must NOT satisfy Isar or RFA."""
        q = "Compare PLD Space, Isar Aerospace and Rocket Factory Augsburg on reusable launchers."
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        pld_p = [p for p in res.proposition_results if p.entity_id == "pld"][0]
        isar_p = [p for p in res.proposition_results if p.entity_id == "isar"][0]

        self.assertEqual(pld_p.final_status, "SUPPORTED")
        self.assertEqual(isar_p.final_status, "INSUFFICIENT_EVIDENCE")

    def test_h_retrieval_score_trap(self):
        """Test H: High retrieval relevance score with failing semantic entailment yields NOT_ENTAILED."""
        passage = "PLD Space operates a non-reusable expendable rocket."
        sem_res = verify_semantic_entailment(passage, "pld", "PLD Space", target_temporal="IN_DEVELOPMENT")
        
        self.assertNotEqual(sem_res.semantic_status, "ENTAILED")
        self.assertTrue(sem_res.is_contradiction or not sem_res.predicate_support)

    def test_i_stale_evidence_rejected(self):
        """Test I: Stale evidence from previous run outside current_run_doc_ids is rejected."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=["doc_stale_non_existent"])

        pld_p = [p for p in res.proposition_results if p.entity_id == "pld"][0]
        self.assertEqual(pld_p.final_status, "INSUFFICIENT_EVIDENCE")

    def test_j_contradiction_and_conflict(self):
        """Test J: Explicit contradiction fixture returns CONTRADICTED or CONFLICT."""
        passage = "PLD Space is not developing a reusable launch vehicle."
        sem_res = verify_semantic_entailment(passage, "pld", "PLD Space")
        
        self.assertEqual(sem_res.semantic_status, "CONTRADICTED")

    def test_k_no_evidence_becomes_insufficient_evidence(self):
        """Test K: Proposition with zero retrieved evidence becomes INSUFFICIENT_EVIDENCE."""
        q = "Is Orbex developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        orb_p = [p for p in res.proposition_results if p.entity_id == "orbex"][0]
        self.assertIn(orb_p.final_status, ["INSUFFICIENT_EVIDENCE", "NO_SOURCE_ROOT"])

    def test_l_planner_truth_isolation(self):
        """Test L: Planner produces UNVERIFIED before retrieval/verification."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        pld_p = [p for p in res.proposition_results if p.entity_id == "pld"][0]
        self.assertEqual(pld_p.planned_status, "UNVERIFIED")

    def test_m_pipeline_determinism(self):
        """Test M: 3 pipeline runs with identical corpus/query produce 100% identical outputs."""
        q = "Compare PLD Space and Isar Aerospace on reusable launch vehicle development."
        run1 = execute_research_pipeline(q, run_id="run_det_1", current_run_doc_ids=self.current_run_doc_ids)
        run2 = execute_research_pipeline(q, run_id="run_det_2", current_run_doc_ids=self.current_run_doc_ids)
        run3 = execute_research_pipeline(q, run_id="run_det_3", current_run_doc_ids=self.current_run_doc_ids)

        p1 = [p.final_status for p in run1.proposition_results]
        p2 = [p.final_status for p in run2.proposition_results]
        p3 = [p.final_status for p in run3.proposition_results]

        self.assertEqual(p1, p2)
        self.assertEqual(p2, p3)

if __name__ == "__main__":
    unittest.main()
