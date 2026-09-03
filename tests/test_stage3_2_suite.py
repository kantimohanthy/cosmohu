import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.proposition_engine import (
    evaluate_proposition_for_entity,
    CandidateProposition,
    extract_temporal_status,
    is_evidence_associated_with_entity
)
from app.services.source_registry import get_source_roots_for_entity, RegisteredSource, source_registry
from app.services.discovery import discover_authoritative_pages
from app.models.schemas import SourceType

class TestStage32Suite(unittest.TestCase):

    def test_a_targeted_discovery(self):
        """Test A: A source root produces relevant internal pages where they exist."""
        test_root = RegisteredSource(
            source_id="src_test_isar",
            publisher="Isar Aerospace",
            source_url="https://isaraerospace.com",
            source_tier="TIER_1",
            source_type=SourceType.WEB,
            entity_scope=["isar"],
            enabled=True
        )
        res = discover_authoritative_pages(test_root, max_pages=3)
        self.assertGreater(len(res["crawled_records"]), 0)
        self.assertIn("root_url", res)

    def test_b_same_domain_enforcement(self):
        """Test B: External links cannot become authoritative company pages accidentally."""
        ev_external = {
            "evidence_id": "EV-ext-01",
            "evidence_text": "Isar Aerospace is developing Spectrum.",
            "source_url": "https://some-unrelated-external-blog.com/post",
            "publisher": "External Blog",
            "source_tier": "TIER_3"
        }
        self.assertFalse(is_evidence_associated_with_entity(ev_external, "pld", "PLD Space"))

    def test_c_proposition_specificity(self):
        """Test C: Generic launch evidence cannot satisfy reusable launch proposition."""
        generic_passage = {
            "evidence_id": "EV-pld-gen",
            "evidence_text": "PLD Space is a European launch service provider manufacturing Miura 5.",
            "confidence": 0.85,
            "document_id": "doc_pld_gen",
            "source_url": "https://www.pldspace.com",
            "publisher": "PLD Space",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [generic_passage], current_run_doc_ids=["doc_pld_gen"])
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_d_temporal_specificity(self):
        """Test D: 'Plans to develop' cannot satisfy 'is operational' proposition."""
        planned_text = "The company plans to develop a reusable first stage in the future."
        temporal = extract_temporal_status(planned_text)
        self.assertEqual(temporal, "PLANNED")

        planned_passage = {
            "evidence_id": "EV-planned-01",
            "evidence_text": planned_text,
            "confidence": 0.85,
            "document_id": "doc_planned",
            "source_url": "https://isaraerospace.com",
            "publisher": "Isar Aerospace",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }

        # Require OPERATIONAL status -> Planned passage must NOT satisfy
        prop = evaluate_proposition_for_entity("isar", "Isar Aerospace", [planned_passage], target_temporal_requirement="OPERATIONAL", current_run_doc_ids=["doc_planned"])
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_e_evidence_traceability(self):
        """Test E: Every SUPPORTED proposition has evidence_id, document_id, source_url, exact passage."""
        reusable_passage = {
            "evidence_id": "EV-supported-101",
            "evidence_text": "Isar Aerospace is developing reusable launch vehicle technology for Spectrum.",
            "confidence": 0.95,
            "document_id": "doc_isar_supp",
            "source_url": "https://isaraerospace.com/technology",
            "publisher": "Isar Aerospace",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }

        prop = evaluate_proposition_for_entity("isar", "Isar Aerospace", [reusable_passage], current_run_doc_ids=["doc_isar_supp"])
        self.assertEqual(prop.verification_status, "SUPPORTED")
        self.assertIsNotNone(prop.evidence_id)
        self.assertIsNotNone(prop.document_id)
        self.assertIsNotNone(prop.source_url)
        self.assertIsNotNone(prop.evidence_text)

    def test_f_redirect_integrity(self):
        """Test F: A redirect mismatch cannot become supported evidence."""
        mismatch_passage = {
            "evidence_id": "EV-mismatch-99",
            "evidence_text": "ArianeGroup - Wikipedia Jump to content (Redirected from MaiaSpace)",
            "confidence": 0.09,
            "document_id": "doc_maia_wiki",
            "source_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "requested_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "final_resolved_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "publisher": "Wikipedia",
            "source_tier": "TIER_4",
            "identity_mismatch": True
        }

        prop = evaluate_proposition_for_entity("maia", "MaiaSpace", [mismatch_passage], current_run_doc_ids=["doc_maia_wiki"])
        self.assertEqual(prop.verification_status, "REDIRECT_MISMATCH")
        self.assertEqual(prop.confidence, 0.0)

    def test_g_entity_isolation(self):
        """Test G: Evidence for one company cannot satisfy another company's proposition."""
        isar_passage = {
            "evidence_id": "EV-isar-only",
            "evidence_text": "Isar Aerospace is developing reusable launch vehicle technology.",
            "confidence": 0.90,
            "document_id": "doc_isar_doc",
            "source_url": "https://isaraerospace.com",
            "publisher": "Isar Aerospace",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }

        prop_rfa = evaluate_proposition_for_entity("rfa", "Rocket Factory Augsburg", [isar_passage], current_run_doc_ids=["doc_isar_doc"])
        self.assertEqual(prop_rfa.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_h_no_source_root(self):
        """Test H: Orbex remains NO_SOURCE_ROOT unless a real authoritative source root is registered."""
        roots = get_source_roots_for_entity("orbex")
        self.assertEqual(len(roots), 0)

        prop_orbex = evaluate_proposition_for_entity("orbex", "Orbex", [])
        self.assertEqual(prop_orbex.verification_status, "NO_SOURCE_ROOT")

if __name__ == "__main__":
    unittest.main()
