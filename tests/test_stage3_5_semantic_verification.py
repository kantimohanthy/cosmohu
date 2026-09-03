import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.semantic_verifier import verify_semantic_entailment
from app.services.proposition_engine import evaluate_proposition_for_entity, CandidateProposition
from app.services.orvyra_adapter import OrvyraAdapter, generate_deterministic_evidence_id
from app.models.schemas import EvidencePassage

class TestStage35SemanticVerification(unittest.TestCase):

    def test_a_explicit_positive_entailment(self):
        """Test A: Explicit positive entailment -> ENTAILED & SUPPORTED."""
        text = "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
        res = verify_semantic_entailment(text, "pld", "PLD Space", target_temporal="IN_DEVELOPMENT")
        
        self.assertEqual(res.semantic_status, "ENTAILED")
        self.assertTrue(res.entity_attribution_verified)
        self.assertTrue(res.predicate_supported)
        self.assertTrue(res.object_concept_supported)
        
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [{"evidence_id": "ev1", "evidence_text": text, "document_id": "doc1", "source_url": "https://www.pldspace.com/en/miura-5.html", "publisher": "PLD Space", "source_tier": "TIER_1"}], current_run_doc_ids=["doc1"])
        self.assertEqual(prop.verification_status, "SUPPORTED")
        self.assertEqual(prop.semantic_status, "ENTAILED")

    def test_b_generic_reusable_statement(self):
        """Test B: Generic statement without entity attribution -> NOT_ENTAILED."""
        text = "Reusable launch vehicles are becoming increasingly important in Europe."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertFalse(res.entity_attribution_verified)
        self.assertEqual(res.failure_component, "entity")
        
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [{"evidence_id": "ev2", "evidence_text": text, "document_id": "doc2", "source_url": "https://www.esa.int", "publisher": "ESA", "source_tier": "TIER_1"}], current_run_doc_ids=["doc2"])
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_c_entity_mention_without_development_predicate(self):
        """Test C: Entity mention without development predicate -> NOT_ENTAILED."""
        text = "PLD Space launched Miura 1 suborbital demonstrator rocket."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertTrue(res.entity_attribution_verified)
        self.assertFalse(res.predicate_supported)
        self.assertEqual(res.failure_component, "predicate")

    def test_d_development_without_reusable_property(self):
        """Test D: Development mention without reusable property -> NOT_ENTAILED."""
        text = "PLD Space is developing a small satellite launch vehicle."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertTrue(res.entity_attribution_verified)
        self.assertTrue(res.predicate_supported)
        self.assertFalse(res.object_concept_supported)
        self.assertEqual(res.failure_component, "object")

    def test_e_reusable_property_without_entity_attribution(self):
        """Test E: Reusable mention without entity attribution -> NOT_ENTAILED."""
        text = "The rocket is designed to be fully reusable."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertFalse(res.entity_attribution_verified)

    def test_f_historical_development_temporal_mismatch(self):
        """Test F: Historical development cannot satisfy current OPERATIONAL proposition."""
        text = "PLD Space previously investigated reusable technologies in 2018."
        res = verify_semantic_entailment(text, "pld", "PLD Space", target_temporal="OPERATIONAL")
        
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertEqual(res.failure_component, "temporal_scope")

    def test_g_explicit_contradiction(self):
        """Test G: Explicit contradiction -> CONTRADICTED."""
        text = "PLD Space abandoned development of Miura 5 reusable launch vehicle."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertEqual(res.semantic_status, "CONTRADICTED")
        self.assertTrue(res.is_contradiction)
        
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [{"evidence_id": "ev_c1", "evidence_text": text, "document_id": "doc_c1", "source_url": "https://news.com", "publisher": "News", "source_tier": "TIER_3"}], current_run_doc_ids=["doc_c1"])
        self.assertEqual(prop.verification_status, "CONTRADICTED")

    def test_h_contradiction_plus_supporting_evidence_yields_conflict(self):
        """Test H: Coexisting supporting and contradicting evidence -> CONFLICT."""
        supporting_text = "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
        contradicting_text = "PLD Space abandoned development of Miura 5 reusable launcher."
        
        passages = [
            {"evidence_id": "ev_supp", "evidence_text": supporting_text, "document_id": "doc_s", "source_url": "https://www.pldspace.com/en/miura-5.html", "publisher": "PLD Space", "source_tier": "TIER_1"},
            {"evidence_id": "ev_contr", "evidence_text": contradicting_text, "document_id": "doc_c", "source_url": "https://spaceblog.com/post1", "publisher": "Blog", "source_tier": "TIER_4"}
        ]
        
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=["doc_s", "doc_c"])
        self.assertEqual(prop.verification_status, "CONFLICT")

    def test_i_cross_entity_evidence_rejected(self):
        """Test I: Cross-entity evidence (PLD passage evaluated for Isar) -> NOT_ENTAILED."""
        pld_text = "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
        res = verify_semantic_entailment(pld_text, "isar", "Isar Aerospace")
        
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertEqual(res.failure_component, "entity")

    def test_j_stale_evidence_rejected(self):
        """Test J: Document outside current_run_doc_ids -> INSUFFICIENT_EVIDENCE."""
        pld_text = "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [{"evidence_id": "ev_stale", "evidence_text": pld_text, "document_id": "doc_old_999", "source_url": "https://www.pldspace.com"}], current_run_doc_ids=["doc_fresh_111"])
        
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_k_redirect_mismatch_rejected(self):
        """Test K: Soft redirect identity mismatch -> REDIRECT_MISMATCH / INVALID_PROVENANCE."""
        redirect_text = "ArianeGroup - Wikipedia Jump to content (Redirected from MaiaSpace)"
        res = verify_semantic_entailment(redirect_text, "maia", "MaiaSpace", identity_mismatch=True)
        
        self.assertEqual(res.semantic_status, "INVALID_PROVENANCE")

    def test_l_multi_source_corroboration_retains_all_evidence_ids(self):
        """Test L: Multi-source corroboration retains both independent evidence IDs."""
        text_a = "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
        text_b = "PLD Space R&D program is building MIURA 5 reusable launcher."
        
        passages = [
            {"evidence_id": "ev_a", "evidence_text": text_a, "document_id": "doc_a", "source_url": "https://www.pldspace.com/en/news/eib-finances.html", "publisher": "PLD Space", "source_tier": "TIER_1"},
            {"evidence_id": "ev_b", "evidence_text": text_b, "document_id": "doc_b", "source_url": "https://www.pldspace.com/en/miura-5.html", "publisher": "PLD Space", "source_tier": "TIER_1"}
        ]
        
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=["doc_a", "doc_b"])
        self.assertEqual(prop.verification_status, "SUPPORTED")
        self.assertEqual(len(prop.evidence_ids), 2)
        self.assertIn("ev_a", prop.evidence_ids)
        self.assertIn("ev_b", prop.evidence_ids)

    def test_m_duplicate_logical_relationship_prevented(self):
        """Test M: Two corroborating passages produce exactly 1 Orvyra relationship edge."""
        passages = [
            EvidencePassage(passage_id="ev_a", chunk_id="chk_a", document_id="doc_a", source_id="src_pld", title="PLD Space", publisher="PLD Space", source_url="https://www.pldspace.com/en/news/eib-finances.html", text="PLD Space is developing MIURA 5, an orbital reusable launch vehicle.", relevance_score=0.95, confidence_score=0.95, why_relevant="Match"),
            EvidencePassage(passage_id="ev_b", chunk_id="chk_b", document_id="doc_b", source_id="src_pld", title="PLD Space", publisher="PLD Space", source_url="https://www.pldspace.com/en/miura-5.html", text="PLD Space R&D program is building MIURA 5 reusable launcher.", relevance_score=0.92, confidence_score=0.92, why_relevant="Match")
        ]
        
        doc_map = {
            "doc_a": {"content_hash": "hash_a", "version": 1, "publisher": "PLD Space", "source_url": "https://www.pldspace.com/en/news/eib-finances.html", "extra": {"source_tier": "TIER_1"}},
            "doc_b": {"content_hash": "hash_b", "version": 1, "publisher": "PLD Space", "source_url": "https://www.pldspace.com/en/miura-5.html", "extra": {"source_tier": "TIER_1"}}
        }
        
        resp = OrvyraAdapter.build_vertical_slice("PLD reusable launcher", {}, passages, doc_map, {}, run_id="run_m")
        self.assertEqual(len(resp.edges), 1, "FAIL: Duplicate Orvyra edges created!")
        self.assertEqual(resp.edges[0].from_id, "pld")
        self.assertEqual(resp.edges[0].to_id, "reusable")
        self.assertGreaterEqual(len(resp.edges[0].ev), 2)

    def test_n_fragmentary_keyword_passage_rejected(self):
        """Test N: Fragmentary keyword passage without complete compositional predicate -> NOT_ENTAILED."""
        frag_text = "PLD Space launch vehicle technology reusable."
        res = verify_semantic_entailment(frag_text, "pld", "PLD Space")
        
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertEqual(res.failure_component, "predicate")

if __name__ == "__main__":
    unittest.main()
