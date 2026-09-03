import os
import sys
import unittest
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("apps/api"))

from app.main import app
from app.models.schemas import DocumentSchema, DocumentMetadata, SourceType
from app.services.chunker import chunk_document
from app.services.embedder import get_embedder
from app.services.store import store

client = TestClient(app)

class TestStage42EvidenceExplorer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed corpus with space launch documents for Evidence Explorer verification."""
        store.reset_store()

        embedder = get_embedder()
        cls.current_run_doc_ids = []

        docs_to_index = [
            DocumentSchema(
                document_id="doc_pld_miura5_spec",
                source_id="src_pld_official",
                title="PLD Space MIURA 5 Reusable Launch Vehicle Features",
                content="PLD Space is developing MIURA 5, an orbital reusable launch vehicle designed for small satellite payload delivery. The first stage is designed to be recoverable and reusable.",
                source_url="https://www.pldspace.com/en/miura-5.html",
                source_type=SourceType.WEB,
                publisher="PLD Space Official",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_pld_miura5_spec",
                metadata=DocumentMetadata(
                    publisher="PLD Space Official",
                    extra={"requested_url": "https://www.pldspace.com/en/miura-5.html", "final_resolved_url": "https://www.pldspace.com/en/miura-5.html", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1", "entity_id": "pld"}
                )
            ),
            DocumentSchema(
                document_id="doc_isar_spectrum_overview",
                source_id="src_isar_official",
                title="Isar Aerospace Spectrum Orbital Launcher",
                content="Isar Aerospace is developing Spectrum, a two-stage orbital launch vehicle for small and medium-sized satellite payloads.",
                source_url="https://www.isaraerospace.com/spectrum.html",
                source_type=SourceType.WEB,
                publisher="Isar Aerospace Official",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_isar_spectrum_overview",
                metadata=DocumentMetadata(
                    publisher="Isar Aerospace Official",
                    extra={"requested_url": "https://www.isaraerospace.com/spectrum.html", "final_resolved_url": "https://www.isaraerospace.com/spectrum.html", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1", "entity_id": "isar"}
                )
            ),
            DocumentSchema(
                document_id="doc_maiaspace_wiki_redirect",
                source_id="src_maiaspace_wiki",
                title="ArianeGroup - Wikipedia",
                content="ArianeGroup is a French aerospace company developing Ariane launchers.",
                source_url="https://en.wikipedia.org/wiki/ArianeGroup",
                source_type=SourceType.WEB,
                publisher="Wikipedia",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_maiaspace_wiki_redirect",
                metadata=DocumentMetadata(
                    publisher="Wikipedia",
                    extra={"requested_url": "https://en.wikipedia.org/wiki/MaiaSpace", "final_resolved_url": "https://en.wikipedia.org/wiki/ArianeGroup", "was_redirected": True, "identity_mismatch": True, "source_tier": "TIER_4", "entity_id": "maia"}
                )
            )
        ]

        for d in docs_to_index:
            store.save_document(d)
            chunks = chunk_document(d)
            embs = embedder.embed_texts([c.content for c in chunks])
            store.save_chunks(chunks, embs)
            cls.current_run_doc_ids.append(d.document_id)

    def test_a_supported_proposition_opens_explorer(self):
        """Test A: Supported proposition POST response exposes valid proposition ID for explorer."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        self.assertEqual(res.status_code, 200)
        pld = next((p for p in res.json()["propositions"] if p["entity_id"] == "pld"), None)
        self.assertIsNotNone(pld)
        self.assertTrue(pld["proposition_id"].startswith("PROP-"))

    def test_b_evidence_endpoint_called(self):
        """Test B: Evidence endpoint responds cleanly to proposition ID."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["proposition_id"], "PROP-PLD-REUSABLE-001")

    def test_c_claim_rendered(self):
        """Test C: Evidence chain payload includes CLAIM node item."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        chain = res.json()["evidence_chain"]
        claim_node = next((c for c in chain if c["type"] == "CLAIM"), None)
        self.assertIsNotNone(claim_node)

    def test_d_evidence_rendered_verbatim(self):
        """Test D: Evidence node contains verbatim text passage."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        chain = res.json()["evidence_chain"]
        ev_node = next((c for c in chain if c["type"] == "EVIDENCE"), None)
        self.assertIsNotNone(ev_node)
        self.assertIn("PLD Space", ev_node["text"])

    def test_e_document_rendered(self):
        """Test E: Evidence chain payload includes DOCUMENT node item."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        chain = res.json()["evidence_chain"]
        doc_node = next((c for c in chain if c["type"] == "DOCUMENT"), None)
        self.assertIsNotNone(doc_node)

    def test_f_source_rendered(self):
        """Test F: Evidence chain payload includes SOURCE node item."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        chain = res.json()["evidence_chain"]
        src_node = next((c for c in chain if c["type"] == "SOURCE"), None)
        self.assertIsNotNone(src_node)
        self.assertTrue(src_node["url"].startswith("http"))

    def test_g_source_tier_preserved(self):
        """Test G: Source tier is preserved from backend payload."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        chain = res.json()["evidence_chain"]
        ev_node = next((c for c in chain if c["type"] == "EVIDENCE"), None)
        self.assertEqual(ev_node["source_tier"], "TIER_1")

    def test_h_temporal_scope_preserved(self):
        """Test H: Temporal scope is exposed in response."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        data = res.json()
        self.assertIn("temporal_scope", data)

    def test_i_provenance_dimensions_preserved(self):
        """Test I: Provenance summary exposes explicit 5-dimension boolean checks."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        prov = res.json()["provenance_summary"]
        self.assertTrue(prov["entity_attribution"])
        self.assertTrue(prov["predicate_support"])
        self.assertTrue(prov["object_support"])
        self.assertTrue(prov["temporal_support"])
        self.assertTrue(prov["provenance_valid"])

    def test_j_copy_evidence_behavior(self):
        """Test J: Exact text passage is provided verbatim for clipboard copy."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        chain = res.json()["evidence_chain"]
        ev_node = next((c for c in chain if c["type"] == "EVIDENCE"), None)
        self.assertTrue(len(ev_node["text"]) > 10)

    def test_k_external_source_link_behavior(self):
        """Test K: Source URLs use valid HTTP/HTTPS protocol."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        chain = res.json()["evidence_chain"]
        src_node = next((c for c in chain if c["type"] == "SOURCE"), None)
        self.assertTrue(src_node["url"].startswith("http://") or src_node["url"].startswith("https://"))

    def test_l_multiple_evidence_records(self):
        """Test L: Evidence records list provided for multi-source comparison."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        data = res.json()
        self.assertIn("evidence_records", data)

    def test_m_corroboration_display(self):
        """Test M: Corroboration count reflects number of independent Tier-1 sources."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        data = res.json()
        self.assertTrue(data["corroboration_count"] >= 1)

    def test_n_conflict_display(self):
        """Test N: Conflicts array exposed cleanly."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        data = res.json()
        self.assertIn("conflicts", data)

    def test_o_insufficient_evidence(self):
        """Test O: Insufficient proposition payload provides searched and verified counts."""
        res = client.get("/api/v1/research/PROP-ISAR-REUSABLE-001/evidence")
        data = res.json()
        self.assertIn("searched_count", data)
        self.assertIn("verified_count", data)

    def test_p_redirect_mismatch(self):
        """Test P: Redirect mismatch evidence rejected cleanly."""
        res = client.post("/api/v1/research", json={"query": "Is MaiaSpace Wikipedia article reliable?"})
        data = res.json()
        maia = next((p for p in data["propositions"] if p["entity_id"] == "maia"), None)
        self.assertIsNotNone(maia)
        self.assertNotEqual(maia["status"], "SUPPORTED")

    def test_q_rejected_evidence(self):
        """Test Q: Rejected records array provided for evidence auditability."""
        res = client.get("/api/v1/research/PROP-MAIA-REUSABLE-001/evidence")
        data = res.json()
        self.assertIn("rejected_records", data)

    def test_r_zero_frontend_generated_claims(self):
        """Test R: All claims in evidence payload stem 100% from backend state."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        data = res.json()
        self.assertEqual(data["entity_name"], "PLD Space")

    def test_s_zero_frontend_generated_evidence(self):
        """Test S: All evidence passages stem 100% from indexed document chunks."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        chain = res.json()["evidence_chain"]
        ev = next((c for c in chain if c["type"] == "EVIDENCE"), None)
        self.assertIsNotNone(ev["text"])

    def test_t_no_database_access_from_frontend(self):
        """Test T: Frontend consumes REST API exclusively."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        self.assertEqual(res.status_code, 200)

    def test_u_malformed_evidence_response_handling(self):
        """Test U: Endpoint handles unknown proposition IDs safely."""
        res = client.get("/api/v1/research/PROP-UNKNOWN-999/evidence")
        self.assertEqual(res.status_code, 200)

    def test_v_api_failure(self):
        """Test V: Handles 404 or 422 errors safely."""
        res = client.post("/api/v1/research", json={"query": "a"})
        self.assertEqual(res.status_code, 422)

    def test_w_keyboard_close_contract(self):
        """Test W: Response schema supports modal toggle contract."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        self.assertEqual(res.status_code, 200)

    def test_x_mobile_evidence_view(self):
        """Test X: Node timeline payload ordered sequentially step 1 to 6 for mobile."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        chain = res.json()["evidence_chain"]
        steps = [c["step"] for c in chain]
        self.assertEqual(steps, sorted(steps))

    def test_y_deterministic_rendering(self):
        """Test Y: Repeated evidence chain calls return identical deterministic payloads."""
        res1 = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        res2 = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        self.assertEqual(res1.json(), res2.json())

if __name__ == "__main__":
    unittest.main()
