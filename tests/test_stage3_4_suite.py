import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.proposition_engine import (
    evaluate_proposition_for_entity,
    is_evidence_associated_with_entity,
    CandidateProposition
)
from app.services.orvyra_adapter import OrvyraAdapter, generate_deterministic_evidence_id
from app.models.schemas import EvidencePassage

class TestStage34Suite(unittest.TestCase):

    def test_a_pld_evidence_cannot_support_isar(self):
        """Test A: PLD Space evidence MUST NOT support Isar Aerospace proposition."""
        pld_passage = {
            "evidence_id": "ev_chk_pld01",
            "evidence_text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle.",
            "confidence": 0.95,
            "document_id": "doc_pld_01",
            "source_url": "https://www.pldspace.com/en/miura-5.html",
            "publisher": "PLD Space",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        prop = evaluate_proposition_for_entity("isar", "Isar Aerospace", [pld_passage], current_run_doc_ids=["doc_pld_01"])
        self.assertNotEqual(prop.verification_status, "SUPPORTED", "FAIL: Cross-entity contamination: PLD evidence supported Isar!")
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_b_isar_evidence_cannot_support_rfa(self):
        """Test B: Isar Aerospace evidence MUST NOT support Rocket Factory Augsburg proposition."""
        isar_passage = {
            "evidence_id": "ev_chk_isar01",
            "evidence_text": "Isar Aerospace is developing Spectrum, a two-stage orbital launch vehicle.",
            "confidence": 0.90,
            "document_id": "doc_isar_01",
            "source_url": "https://www.isaraerospace.com",
            "publisher": "Isar Aerospace",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        prop = evaluate_proposition_for_entity("rfa", "Rocket Factory Augsburg", [isar_passage], current_run_doc_ids=["doc_isar_01"])
        self.assertNotEqual(prop.verification_status, "SUPPORTED", "FAIL: Cross-entity contamination: Isar evidence supported RFA!")
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_c_rfa_evidence_cannot_support_orbex(self):
        """Test C: RFA evidence MUST NOT support Orbex proposition."""
        rfa_passage = {
            "evidence_id": "ev_chk_rfa01",
            "evidence_text": "Rocket Factory Augsburg is developing RFA One launcher.",
            "confidence": 0.90,
            "document_id": "doc_rfa_01",
            "source_url": "https://www.rfa.space",
            "publisher": "Rocket Factory Augsburg",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        prop = evaluate_proposition_for_entity("orbex", "Orbex", [rfa_passage], current_run_doc_ids=["doc_rfa_01"])
        self.assertEqual(prop.verification_status, "NO_SOURCE_ROOT")

    def test_d_generic_statement_cannot_become_entity_proposition(self):
        """Test D: Generic statement about reusable launch vehicles without company context returns INSUFFICIENT_EVIDENCE."""
        generic_passage = {
            "evidence_id": "ev_chk_gen01",
            "evidence_text": "Reusable launch vehicles reduce space transportation costs significantly.",
            "confidence": 0.88,
            "document_id": "doc_gen_01",
            "source_url": "https://www.esa.int/Space_Transportation",
            "publisher": "ESA",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        prop = evaluate_proposition_for_entity("isar", "Isar Aerospace", [generic_passage], current_run_doc_ids=["doc_gen_01"])
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE", "FAIL: Generic passage supported entity proposition!")

    def test_e_multi_company_mention_isolation(self):
        """Test E: Evidence mentioning multiple companies attributed ONLY when passage explicitly supports target entity."""
        multi_passage = {
            "evidence_id": "ev_chk_multi01",
            "evidence_text": "PLD Space and Isar Aerospace are European launch startups. PLD Space is developing MIURA 5, an orbital reusable launch vehicle.",
            "confidence": 0.92,
            "document_id": "doc_news_01",
            "source_url": "https://europeanspaceflight.com/news",
            "publisher": "European Spaceflight",
            "source_tier": "TIER_3",
            "identity_mismatch": False
        }
        
        # Evaluated for Isar Aerospace -> must return INSUFFICIENT_EVIDENCE because reusability is predicated for PLD Space
        prop_isar = evaluate_proposition_for_entity("isar", "Isar Aerospace", [multi_passage], current_run_doc_ids=["doc_news_01"])
        self.assertNotEqual(prop_isar.verification_status, "SUPPORTED")
        
        # Evaluated for PLD Space -> returns SUPPORTED
        prop_pld = evaluate_proposition_for_entity("pld", "PLD Space", [multi_passage], current_run_doc_ids=["doc_news_01"])
        self.assertEqual(prop_pld.verification_status, "SUPPORTED")

    def test_f_no_source_root_returned(self):
        """Test F: Entity with no source root must return NO_SOURCE_ROOT."""
        prop = evaluate_proposition_for_entity("orbex", "Orbex", [], current_run_doc_ids=[])
        self.assertEqual(prop.verification_status, "NO_SOURCE_ROOT")

    def test_g_historical_evidence_cannot_satisfy_current_operational(self):
        """Test G: Historical test flight passage cannot satisfy OPERATIONAL proposition."""
        hist_passage = {
            "evidence_id": "ev_chk_hist01",
            "evidence_text": "PLD Space conducted suborbital test flight of MIURA 1 demonstrator in 2023.",
            "confidence": 0.90,
            "document_id": "doc_pld_hist",
            "source_url": "https://www.pldspace.com/en/news/miura-1-sn1-test-flight.html",
            "publisher": "PLD Space",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [hist_passage], target_temporal_requirement="OPERATIONAL", current_run_doc_ids=["doc_pld_hist"])
        self.assertNotEqual(prop.verification_status, "SUPPORTED")

    def test_h_redirect_mismatch_rejected(self):
        """Test H: Soft redirect / identity mismatch MUST return REDIRECT_MISMATCH."""
        redirect_passage = {
            "evidence_id": "ev_chk_redir01",
            "evidence_text": "ArianeGroup - Wikipedia Jump to content (Redirected from MaiaSpace)",
            "confidence": 0.05,
            "document_id": "doc_maia_wiki",
            "source_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "requested_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "final_resolved_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "publisher": "Wikipedia",
            "source_tier": "TIER_4",
            "identity_mismatch": True
        }
        
        prop = evaluate_proposition_for_entity("maia", "MaiaSpace", [redirect_passage], current_run_doc_ids=["doc_maia_wiki"])
        self.assertEqual(prop.verification_status, "REDIRECT_MISMATCH")

    def test_i_stale_documents_rejected(self):
        """Test I: Documents outside current_run_doc_ids MUST NOT support current run."""
        stale_passage = {
            "evidence_id": "ev_chk_stale77",
            "evidence_text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle.",
            "confidence": 0.95,
            "document_id": "doc_old_historical_999",
            "source_url": "https://www.pldspace.com/en/miura-5.html",
            "publisher": "PLD Space",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [stale_passage], current_run_doc_ids=["doc_fresh_2026"])
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_j_unsupported_proposition_creates_zero_relationships(self):
        """Test J: Unsupported proposition MUST NOT create any Orvyra relationship edge."""
        resp = OrvyraAdapter.build_vertical_slice(
            query="Isar Aerospace reusable launcher",
            query_plan={"intent": "DISCOVERY"},
            retrieved_passages=[],
            doc_map={},
            retrieval_stats={},
            run_id="run_test_j"
        )
        
        self.assertEqual(len(resp.edges), 0, "FAIL: Relationship created without evidence!")
        self.assertTrue(any(w.entity_id == "isar" for w in resp.withheld))

if __name__ == "__main__":
    unittest.main()
