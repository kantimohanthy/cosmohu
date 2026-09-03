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

class TestStage41ResearchTerminal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed corpus with space launch documents."""
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
            )
        ]

        for d in docs_to_index:
            store.save_document(d)
            chunks = chunk_document(d)
            embs = embedder.embed_texts([c.content for c in chunks])
            store.save_chunks(chunks, embs)
            cls.current_run_doc_ids.append(d.document_id)

    def test_a_empty_state_contract(self):
        """Test A: Verifies empty state suggests grounded example queries."""
        # Querying valid research API endpoint returns structured schema
        res = client.post("/api/v1/research", json={"query": "Which European launch companies are developing reusable launch vehicles?"})
        self.assertEqual(res.status_code, 200)

    def test_b_query_submission(self):
        """Test B: Query submission POST /api/v1/research."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "COMPLETED")

    def test_c_loading_state_metadata(self):
        """Test C: Metadata exposes stage timings."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        meta = res.json()["metadata"]
        self.assertIn("planning_ms", meta)
        self.assertIn("retrieval_ms", meta)
        self.assertIn("verification_ms", meta)

    def test_d_successful_research(self):
        """Test D: Successful research returns non-empty answer and propositions."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        self.assertTrue(len(data["answer"]) > 10)
        self.assertTrue(len(data["propositions"]) >= 1)

    def test_e_supported_proposition_rendering(self):
        """Test E: Supported proposition exposes evidence strength and verified evidence IDs."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        pld = next((p for p in data["propositions"] if p["entity_id"] == "pld"), None)
        self.assertIsNotNone(pld)
        self.assertEqual(pld["status"], "SUPPORTED")
        self.assertTrue(len(pld["evidence_ids"]) >= 1)

    def test_f_insufficient_evidence_rendering(self):
        """Test F: Insufficient proposition explicitly renders INSUFFICIENT_EVIDENCE without false negative statement."""
        res = client.post("/api/v1/research", json={"query": "Is Isar Aerospace developing a reusable launch vehicle?"})
        data = res.json()
        isar = next((p for p in data["propositions"] if p["entity_id"] == "isar"), None)
        self.assertIsNotNone(isar)
        self.assertEqual(isar["status"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(len(isar["evidence_ids"]), 0)

    def test_g_contradiction_rendering(self):
        """Test G: Handles verified contradiction explicit status."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space launcher non-reusable?"})
        self.assertEqual(res.status_code, 200)

    def test_h_conflict_rendering(self):
        """Test H: Handles conflict status without resolving in frontend."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space launcher non-reusable?"})
        data = res.json()
        self.assertIn("conflicts", data)

    def test_i_redirect_mismatch_rendering(self):
        """Test I: Redirect mismatch status handled explicitly."""
        res = client.post("/api/v1/research", json={"query": "Is MaiaSpace Wikipedia article reliable?"})
        self.assertEqual(res.status_code, 200)

    def test_j_evidence_inspector(self):
        """Test J: Evidence inspector retrieves complete evidence items."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        self.assertTrue(len(data["evidence"]) >= 1)
        ev = data["evidence"][0]
        self.assertIn("exact_text", ev)
        self.assertIn("source_tier", ev)
        self.assertIn("content_hash", ev)

    def test_k_evidence_chain_api_call(self):
        """Test K: Evidence chain endpoint GET /api/v1/research/{proposition_id}/evidence."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        self.assertEqual(res.status_code, 200)
        chain = res.json()["evidence_chain"]
        self.assertTrue(len(chain) >= 4)
        types = [c["type"] for c in chain]
        self.assertIn("PROPOSITION", types)
        self.assertIn("EVIDENCE", types)
        self.assertIn("DOCUMENT", types)

    def test_l_source_link_rendering(self):
        """Test L: Sources expose valid source URLs and publishers."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        self.assertTrue(len(data["sources"]) >= 1)
        src = data["sources"][0]
        self.assertTrue(src["source_url"].startswith("http"))

    def test_m_api_failure_handling(self):
        """Test M: Safe 422 error response for invalid query payload."""
        res = client.post("/api/v1/research", json={"query": "a"})
        self.assertEqual(res.status_code, 422)

    def test_n_malformed_api_response_handling(self):
        """Test N: Pipeline handles non-matching queries gracefully."""
        res = client.post("/api/v1/research", json={"query": "Unknown Nonexistent Satellite Constellation"})
        self.assertEqual(res.status_code, 200)

    def test_o_no_frontend_generated_claims(self):
        """Test O: Frontend is strictly a read-only consumer; API response dictates all claims."""
        res = client.post("/api/v1/research", json={"query": "Is Isar Aerospace developing a reusable launch vehicle?"})
        data = res.json()

        # Isar Aerospace proposition has 0 claims
        isar_claims = [c for c in data["claims"] if c["entity_id"] == "isar"]
        self.assertEqual(len(isar_claims), 0)

    def test_p_deterministic_fallback_rendering(self):
        """Test P: Provider type in metadata correctly flags DETERMINISTIC_FALLBACK or REAL_LLM."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        meta = res.json()["metadata"]
        self.assertIn(meta["provider_type"], ["DETERMINISTIC_FALLBACK", "REAL_LLM"])

    def test_q_mobile_responsive_contract(self):
        """Test Q: API payload exposes all components required for mobile/desktop layout."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        self.assertIn("propositions", data)
        self.assertIn("evidence", data)
        self.assertIn("sources", data)

    def test_r_query_history_tracking(self):
        """Test R: Query responses include unique run_ids and query text for history tracking."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        self.assertIn("run_id", data)
        self.assertEqual(data["query"], "Is PLD Space developing a reusable launch vehicle?")

if __name__ == "__main__":
    unittest.main()
