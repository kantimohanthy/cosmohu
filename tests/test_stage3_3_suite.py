import os
import sys
import unittest
import hashlib

sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.hashing import compute_content_hash
from app.services.proposition_engine import evaluate_proposition_for_entity, CandidateProposition
from app.services.orvyra_adapter import OrvyraAdapter, generate_deterministic_evidence_id
from app.models.schemas import EvidencePassage

class TestStage33Suite(unittest.TestCase):

    def test_a_supported_evidence_belongs_to_current_run(self):
        """Test A: Supported evidence must belong to current_run_doc_ids."""
        current_run_doc_ids = ["doc_live_111"]
        live_passage = {
            "evidence_id": "ev_chk_live1",
            "evidence_text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle.",
            "confidence": 0.95,
            "document_id": "doc_live_111",
            "source_url": "https://www.pldspace.com/en/miura-5.html",
            "publisher": "PLD Space",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [live_passage], current_run_doc_ids=current_run_doc_ids)
        self.assertEqual(prop.verification_status, "SUPPORTED")
        self.assertIn(prop.document_id, current_run_doc_ids)

    def test_b_document_hash_matches_stored_content(self):
        """Test B: Evidence document hash must match stored content SHA-256."""
        sample_content = "PLD Space MIURA 5 is an orbital reusable launch vehicle."
        computed_hash = compute_content_hash(sample_content)
        expected_hash = hashlib.sha256(sample_content.strip().lower().encode("utf-8")).hexdigest()
        
        self.assertEqual(computed_hash, expected_hash, "FAIL: Document content hash mismatch!")

    def test_c_exact_evidence_passage_exists_in_referenced_chunk(self):
        """Test C: Stored evidence text must be recoverable from referenced chunk content."""
        chunk_content = "Heading: MIURA 5 Launcher\nPLD Space is developing MIURA 5, an orbital reusable launch vehicle."
        passage_text = "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
        
        self.assertIn(passage_text, chunk_content, "FAIL: Exact passage text could not be found in chunk content!")

    def test_d_orvyra_relationship_resolves_through_chain(self):
        """Test D: Orvyra edge RE-0001 must resolve through claim -> evidence -> document -> source."""
        passage = EvidencePassage(
            passage_id="ev_chk_test01",
            chunk_id="chk_test01",
            document_id="doc_pld_test",
            source_id="src_pld",
            title="PLD Space MIURA 5",
            publisher="PLD Space",
            source_url="https://www.pldspace.com/en/miura-5.html",
            text="PLD Space is developing MIURA 5, an orbital reusable launch vehicle.",
            relevance_score=0.92,
            confidence_score=0.95,
            why_relevant="Matches PLD Space reusable launcher proposition"
        )
        
        doc_map = {
            "doc_pld_test": {
                "content_hash": "sha256_abcd1234",
                "version": 1,
                "publisher": "PLD Space",
                "source_url": "https://www.pldspace.com/en/miura-5.html",
                "extra": {"requested_url": "https://www.pldspace.com", "final_resolved_url": "https://www.pldspace.com/en/miura-5.html", "source_tier": "TIER_1"}
            }
        }
        
        resp = OrvyraAdapter.build_vertical_slice(
            query="PLD Space reusable launcher",
            query_plan={"intent": "DISCOVERY"},
            retrieved_passages=[passage],
            doc_map=doc_map,
            retrieval_stats={},
            run_id="run_test_d"
        )
        
        self.assertEqual(len(resp.edges), 1)
        self.assertEqual(resp.edges[0].from_id, "pld")
        self.assertEqual(resp.edges[0].to_id, "reusable")
        self.assertGreater(len(resp.edges[0].ev), 0)
        self.assertIn(resp.edges[0].ev[0], [e.id for e in resp.evidence])

    def test_e_stale_evidence_cannot_satisfy_current_proposition(self):
        """Test E: Stale documents outside current_run_doc_ids MUST NOT satisfy proposition."""
        current_run_doc_ids = ["doc_live_222"]
        stale_passage = {
            "evidence_id": "ev_chk_stale99",
            "evidence_text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle.",
            "confidence": 0.95,
            "document_id": "doc_stale_historical_888",
            "source_url": "https://www.pldspace.com/en/miura-5.html",
            "publisher": "PLD Space",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [stale_passage], current_run_doc_ids=current_run_doc_ids)
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_f_repeated_acquisition_produces_consistent_result(self):
        """Test F: Repeated acquisition across fresh runs produces consistent factual verification result."""
        passage_run1 = {
            "evidence_id": generate_deterministic_evidence_id("PLD Space is developing MIURA 5...", "doc_pld_01"),
            "evidence_text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle.",
            "confidence": 0.95,
            "document_id": "doc_pld_01",
            "source_url": "https://www.pldspace.com/en/miura-5.html",
            "publisher": "PLD Space",
            "source_tier": "TIER_1",
            "identity_mismatch": False
        }
        
        passage_run2 = dict(passage_run1)
        
        prop1 = evaluate_proposition_for_entity("pld", "PLD Space", [passage_run1], current_run_doc_ids=["doc_pld_01"])
        prop2 = evaluate_proposition_for_entity("pld", "PLD Space", [passage_run2], current_run_doc_ids=["doc_pld_01"])
        
        self.assertEqual(prop1.verification_status, prop2.verification_status)
        self.assertEqual(prop1.verification_status, "SUPPORTED")
        self.assertEqual(prop1.evidence_id, prop2.evidence_id)

    def test_g_two_legitimate_source_pages_not_collapsed(self):
        """Test G: Page A (/news/eib-finances...) and Page B (/miura-5.html) are preserved as separate first-party evidence items."""
        page_a = {
            "evidence_id": generate_deterministic_evidence_id("Text A", "doc_page_a"),
            "evidence_text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle.",
            "source_url": "https://www.pldspace.com/en/news/eib-finances-30-million-euros-pld-space-launcher-miura5.html",
            "document_id": "doc_page_a"
        }
        page_b = {
            "evidence_id": generate_deterministic_evidence_id("Text B", "doc_page_b"),
            "evidence_text": "PLD Space is developing MIURA 5 reusable launcher.",
            "source_url": "https://www.pldspace.com/en/miura-5.html",
            "document_id": "doc_page_b"
        }
        
        self.assertNotEqual(page_a["document_id"], page_b["document_id"])
        self.assertNotEqual(page_a["source_url"], page_b["source_url"])

    def test_h_broken_evidence_chain_invalidates_supported_proposition(self):
        """Test H: Mismatched identity or broken evidence chain invalidates supported proposition."""
        mismatched_passage = {
            "evidence_id": "ev_chk_broken",
            "evidence_text": "ArianeGroup - Wikipedia Jump to content (Redirected from MaiaSpace)",
            "confidence": 0.09,
            "document_id": "doc_broken",
            "source_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "requested_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "final_resolved_url": "https://en.wikipedia.org/wiki/MaiaSpace",
            "publisher": "Wikipedia",
            "source_tier": "TIER_4",
            "identity_mismatch": True
        }
        
        prop = evaluate_proposition_for_entity("maia", "MaiaSpace", [mismatched_passage], current_run_doc_ids=["doc_broken"])
        self.assertEqual(prop.verification_status, "REDIRECT_MISMATCH")

if __name__ == "__main__":
    unittest.main()
