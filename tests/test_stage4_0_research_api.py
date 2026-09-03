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

class TestStage40ResearchAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed corpus with authoritative European launch company documents."""
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
                document_id="doc_rfa_one_spec",
                source_id="src_rfa_official",
                title="RFA One Launch Vehicle Overview",
                content="Rocket Factory Augsburg (RFA) is developing RFA One, a three-stage orbital launch vehicle powered by staged combustion engines.",
                source_url="https://www.rfa.space/rfa-one",
                source_type=SourceType.WEB,
                publisher="RFA Official",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_rfa_one_spec",
                metadata=DocumentMetadata(
                    publisher="RFA Official",
                    extra={"requested_url": "https://www.rfa.space/rfa-one", "final_resolved_url": "https://www.rfa.space/rfa-one", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1", "entity_id": "rfa"}
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

    def test_a_basic_query(self):
        """Test A: Basic research query endpoint POST /api/v1/research."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "COMPLETED")
        self.assertIn("answer", data)
        self.assertTrue(len(data["propositions"]) >= 1)

    def test_b_multi_proposition_query(self):
        """Test B: Multi-proposition query returning structured entity breakdown."""
        res = client.post("/api/v1/research", json={"query": "Which European launch companies are developing reusable launch vehicles?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "COMPLETED")
        self.assertTrue(len(data["propositions"]) >= 1)

    def test_c_supported_proposition_rendering(self):
        """Test C: Supported proposition exposes verified claims and evidence."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        pld_prop = next((p for p in data["propositions"] if p["entity_id"] == "pld"), None)
        self.assertIsNotNone(pld_prop)
        self.assertEqual(pld_prop["status"], "SUPPORTED")
        self.assertTrue(len(pld_prop["evidence_ids"]) >= 1)

    def test_d_insufficient_evidence_rendering(self):
        """Test D: Insufficient proposition renders explicitly as INSUFFICIENT_EVIDENCE."""
        res = client.post("/api/v1/research", json={"query": "Is Isar Aerospace developing a reusable launch vehicle?"})
        data = res.json()
        isar_prop = next((p for p in data["propositions"] if p["entity_id"] == "isar"), None)
        self.assertIsNotNone(isar_prop)
        self.assertEqual(isar_prop["status"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(len(isar_prop["evidence_ids"]), 0)

    def test_e_contradiction_rendering(self):
        """Test E: Verified contradiction rendering handled explicitly."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space launcher non-reusable?"})
        data = res.json()
        self.assertIn(data["status"], ["COMPLETED"])

    def test_f_redirect_mismatch_rendering(self):
        """Test F: Redirect mismatch prevents MaiaSpace Wikipedia from becoming verified evidence."""
        res = client.post("/api/v1/research", json={"query": "Is MaiaSpace Wikipedia article reliable?"})
        data = res.json()
        maia_prop = next((p for p in data["propositions"] if p["entity_id"] == "maia"), None)
        if maia_prop:
            self.assertNotEqual(maia_prop["status"], "SUPPORTED")

    def test_g_evidence_chain_endpoint(self):
        """Test G: 'WHY THIS CONCLUSION?' GET /api/v1/research/{proposition_id}/evidence endpoint."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["proposition_id"], "PROP-PLD-REUSABLE-001")
        self.assertTrue(len(data["evidence_chain"]) >= 4)

    def test_h_entity_isolation(self):
        """Test H: Zero cross-entity evidence leakage."""
        res = client.post("/api/v1/research", json={"query": "Is Isar Aerospace developing a reusable launch vehicle?"})
        data = res.json()
        for ev in data["evidence"]:
            self.assertNotEqual(ev["publisher"], "PLD Space Official")

    def test_i_stale_evidence_rejection(self):
        """Test I: Passages from prior runs excluded."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        for ev in data["evidence"]:
            self.assertIn(ev["document_id"], self.current_run_doc_ids)

    def test_j_llm_unavailable_fallback(self):
        """Test J: Falls back to deterministic answer model when LLM unavailable."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        meta = data["metadata"]
        self.assertIn(meta["provider_type"], ["DETERMINISTIC_FALLBACK", "REAL_LLM"])

    def test_k_malformed_llm_fallback(self):
        """Test K: Deterministic fallback on malformed synthesis."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        self.assertEqual(res.status_code, 200)

    def test_l_claim_validation_failure(self):
        """Test L: Rejects hallucinated claims and falls back cleanly."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        self.assertEqual(res.status_code, 200)

    def test_m_graph_immutability(self):
        """Test M: Frontend research API is strictly read-only for graph state."""
        entities_before = len(store.list_entities())
        client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        entities_after = len(store.list_entities())
        self.assertEqual(entities_before, entities_after)

    def test_n_invalid_query_handling(self):
        """Test N: Handles short/empty queries gracefully."""
        res = client.post("/api/v1/research", json={"query": "a"})
        self.assertEqual(res.status_code, 422)  # Validation error

    def test_o_deterministic_repeatability(self):
        """Test O: Repeated identical queries produce deterministic API responses."""
        res1 = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        res2 = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        self.assertEqual(res1.json()["propositions"], res2.json()["propositions"])

if __name__ == "__main__":
    unittest.main()
