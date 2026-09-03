import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.proposition_engine import evaluate_proposition_for_entity, CandidateProposition, is_evidence_associated_with_entity
from app.services.source_registry import get_source_roots_for_entity

class TestStage31Integrity(unittest.TestCase):

    def test_a_cross_entity_contamination(self):
        """Test A: MaiaSpace redirect mismatch must NOT mark Isar Aerospace as REDIRECT_MISMATCH."""
        maia_mismatch_passage = {
            "evidence_id": "EV-maia-mismatch",
            "evidence_text": "ArianeGroup - Wikipedia Jump to content From Wikipedia... (Redirected from MaiaSpace)",
            "confidence": 0.09,
            "document_id": "doc_maia_wiki",
            "source_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "publisher": "Wikipedia",
            "source_tier": "TIER_4",
            "requested_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "final_resolved_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "identity_mismatch": True
        }
        
        # Pass MaiaSpace mismatch passage to Isar Aerospace proposition evaluation
        prop_isar = evaluate_proposition_for_entity("isar", "Isar Aerospace", [maia_mismatch_passage], current_run_doc_ids=["doc_maia_wiki"])
        
        # Assert Isar Aerospace is NOT marked as REDIRECT_MISMATCH due to MaiaSpace document!
        self.assertNotEqual(prop_isar.verification_status, "REDIRECT_MISMATCH", "FAIL: Cross-entity contamination occurred! MaiaSpace mismatch was attributed to Isar Aerospace.")
        self.assertEqual(prop_isar.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_b_missing_source_root(self):
        """Test B: An entity without a registered source root (Orbex) must produce NO_SOURCE_ROOT."""
        roots_orbex = get_source_roots_for_entity("orbex")
        self.assertEqual(len(roots_orbex), 0, "Orbex should have 0 registered source roots in this test setup.")
        
        prop_orbex = evaluate_proposition_for_entity("orbex", "Orbex", [])
        self.assertEqual(prop_orbex.verification_status, "NO_SOURCE_ROOT", "FAIL: Entity without source root must return NO_SOURCE_ROOT.")
        self.assertIn("NO_SOURCE_ROOT", prop_orbex.reason)

    def test_c_stale_document_exclusion(self):
        """Test C: A document not belonging to the current run must NOT satisfy a current proposition."""
        stale_passage = {
            "evidence_id": "EV-stale-001",
            "evidence_text": "Isar Aerospace is developing reusable launch vehicle technology.",
            "confidence": 0.95,
            "document_id": "doc_stale_historical_12345",
            "source_url": "https://isaraerospace.com",
            "publisher": "Isar Aerospace",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        current_live_doc_ids = ["doc_live_67890"]
        
        prop = evaluate_proposition_for_entity("isar", "Isar Aerospace", [stale_passage], current_run_doc_ids=current_live_doc_ids)
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE", "FAIL: Stale document satisfied current proposition!")

    def test_d_semantic_inheritance_rejection(self):
        """Test D: 'PLD Space develops launch vehicles' MUST remain INSUFFICIENT_EVIDENCE for reusable launcher proposition."""
        generic_passage = {
            "evidence_id": "EV-pld-generic",
            "evidence_text": "PLD Space is a Spanish aerospace company developing micro launch vehicles for small satellites.",
            "confidence": 0.80,
            "document_id": "doc_pld_live",
            "source_url": "https://www.pldspace.com",
            "publisher": "PLD Space",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        prop_pld = evaluate_proposition_for_entity("pld", "PLD Space", [generic_passage], current_run_doc_ids=["doc_pld_live"])
        self.assertEqual(prop_pld.verification_status, "INSUFFICIENT_EVIDENCE", "FAIL: Semantic inheritance allowed generic launch vehicle text to establish reusability!")

    def test_e_entity_isolation(self):
        """Test E: Evidence retrieved for Isar Aerospace must NEVER satisfy a proposition for PLD Space."""
        isar_reusable_passage = {
            "evidence_id": "EV-isar-reusable",
            "evidence_text": "Isar Aerospace is developing Spectrum, a launch vehicle with reusable first stage technology.",
            "confidence": 0.95,
            "document_id": "doc_isar_live",
            "source_url": "https://isaraerospace.com",
            "publisher": "Isar Aerospace",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        # Try to satisfy PLD Space proposition using Isar Aerospace passage
        prop_pld = evaluate_proposition_for_entity("pld", "PLD Space", [isar_reusable_passage], current_run_doc_ids=["doc_isar_live"])
        self.assertEqual(prop_pld.verification_status, "INSUFFICIENT_EVIDENCE", "FAIL: Entity isolation violated! Isar passage satisfied PLD Space proposition.")

if __name__ == "__main__":
    unittest.main()
