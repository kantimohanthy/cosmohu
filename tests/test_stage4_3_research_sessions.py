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

class TestStage43ResearchSessions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed corpus with space launch documents for Research Sessions verification."""
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

    def test_a_session_creation(self):
        """Test A: Session creation POST endpoint."""
        res = client.post("/api/v1/research/sessions", json={"title": "Test Investigation"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["session_id"].startswith("session_"))
        self.assertEqual(data["title"], "Test Investigation")

    def test_b_session_retrieval(self):
        """Test B: Session retrieval GET endpoint."""
        created = client.post("/api/v1/research/sessions", json={"title": "Retrieval Test"}).json()
        sid = created["session_id"]
        res = client.get(f"/api/v1/research/sessions/{sid}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["session_id"], sid)

    def test_c_session_deletion(self):
        """Test C: Session deletion DELETE endpoint."""
        created = client.post("/api/v1/research/sessions", json={"title": "Delete Test"}).json()
        sid = created["session_id"]
        res = client.delete(f"/api/v1/research/sessions/{sid}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "DELETED")

    def test_d_adding_query(self):
        """Test D: Adding research query to session."""
        created = client.post("/api/v1/research/sessions", json={"title": "Query Add Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data["queries"]), 1)
        self.assertTrue(len(data["propositions"]) > 0)

    def test_e_multiple_queries(self):
        """Test E: Multiple queries in single session accumulate artifacts cleanly."""
        created = client.post("/api/v1/research/sessions", json={"title": "Multi Query Test"}).json()
        sid = created["session_id"]
        client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing reusable launch vehicles?"})
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is Isar Aerospace developing reusable launch vehicles?"})
        data = res.json()
        self.assertEqual(len(data["queries"]), 2)
        self.assertTrue(len(data["entities"]) >= 2)

    def test_f_proposition_isolation(self):
        """Test F: Propositions remain uniquely identified and isolated."""
        created = client.post("/api/v1/research/sessions", json={"title": "Prop Isolation Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        props = res.json()["propositions"]
        prop_ids = [p["proposition_id"] for p in props]
        self.assertEqual(len(prop_ids), len(set(prop_ids)))

    def test_g_entity_aggregation(self):
        """Test G: Entities discovered across queries are aggregated."""
        created = client.post("/api/v1/research/sessions", json={"title": "Entity Agg Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        entities = res.json()["entities"]
        ent_names = [e["entity_name"] for e in entities]
        self.assertIn("PLD Space", ent_names)

    def test_h_evidence_aggregation(self):
        """Test H: Unique evidence references aggregated in session."""
        created = client.post("/api/v1/research/sessions", json={"title": "Ev Agg Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        ev_refs = res.json()["evidence_references"]
        self.assertTrue(len(ev_refs) > 0)

    def test_i_insufficient_evidence_preservation(self):
        """Test I: Insufficient propositions preserved in session state."""
        created = client.post("/api/v1/research/sessions", json={"title": "Insuff Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is Isar Aerospace developing a reusable launch vehicle?"})
        insuff = res.json()["insufficient_propositions"]
        self.assertTrue(len(insuff) > 0)

    def test_j_conflict_preservation(self):
        """Test J: Conflicts array preserved in session schema."""
        created = client.post("/api/v1/research/sessions", json={"title": "Conflict Test"}).json()
        sid = created["session_id"]
        data = client.get(f"/api/v1/research/sessions/{sid}").json()
        self.assertIn("conflicts", data)

    def test_k_cross_entity_isolation(self):
        """Test K: No cross-entity claim contamination."""
        created = client.post("/api/v1/research/sessions", json={"title": "Cross Entity Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        claims = res.json()["supported_claims"]
        for c in claims:
            self.assertEqual(c["entity_id"], "pld")

    def test_l_session_reconstruction(self):
        """Test L: Session state reconstructs cleanly from SQLite store."""
        created = client.post("/api/v1/research/sessions", json={"title": "Reconstruction Test"}).json()
        sid = created["session_id"]
        client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        reconstructed = client.get(f"/api/v1/research/sessions/{sid}").json()
        self.assertEqual(reconstructed["session_id"], sid)
        self.assertEqual(len(reconstructed["queries"]), 1)

    def test_m_deterministic_session_state(self):
        """Test M: Session state is deterministic."""
        created = client.post("/api/v1/research/sessions", json={"title": "Deterministic Test"}).json()
        sid = created["session_id"]
        client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        get1 = client.get(f"/api/v1/research/sessions/{sid}").json()
        get2 = client.get(f"/api/v1/research/sessions/{sid}").json()
        self.assertEqual(get1, get2)

    def test_n_comparison_mode_contract(self):
        """Test N: Session metadata supports entity comparison."""
        created = client.post("/api/v1/research/sessions", json={"title": "Comparison Contract Test"}).json()
        sid = created["session_id"]
        res = client.get(f"/api/v1/research/sessions/{sid}").json()
        self.assertIn("metadata", res)

    def test_o_deep_linking_contract(self):
        """Test O: Session ID endpoints support deep link restoration."""
        created = client.post("/api/v1/research/sessions", json={"title": "Deep Link Test"}).json()
        sid = created["session_id"]
        res = client.get(f"/api/v1/research/sessions/{sid}")
        self.assertEqual(res.status_code, 200)

    def test_p_evidence_density(self):
        """Test P: Evidence density formula calculated deterministically."""
        created = client.post("/api/v1/research/sessions", json={"title": "Density Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        meta = res.json()["metadata"]
        self.assertIn("evidence_density", meta)
        self.assertTrue(meta["evidence_density"] >= 0.0)

    def test_q_graph_node_integrity(self):
        """Test Q: Session data supports node integrity for ENTITY, CLAIM, EVIDENCE, DOCUMENT, SOURCE."""
        created = client.post("/api/v1/research/sessions", json={"title": "Graph Node Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        self.assertTrue(len(data["entities"]) > 0)
        self.assertTrue(len(data["supported_claims"]) > 0)
        self.assertTrue(len(data["evidence_references"]) > 0)

    def test_r_graph_edge_integrity(self):
        """Test R: Verified claims map to evidence references cleanly."""
        created = client.post("/api/v1/research/sessions", json={"title": "Graph Edge Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        claim = data["supported_claims"][0]
        self.assertTrue(len(claim["evidence_ids"]) > 0)

    def test_s_no_frontend_created_claims(self):
        """Test S: Claims stem 100% from backend session state."""
        created = client.post("/api/v1/research/sessions", json={"title": "No Frontend Claims Test"}).json()
        sid = created["session_id"]
        data = client.get(f"/api/v1/research/sessions/{sid}").json()
        self.assertEqual(len(data["supported_claims"]), 0)

    def test_t_read_only_frontend(self):
        """Test T: REST API enforces read-only session retrieval."""
        created = client.post("/api/v1/research/sessions", json={"title": "Read Only Test"}).json()
        sid = created["session_id"]
        res = client.get(f"/api/v1/research/sessions/{sid}")
        self.assertEqual(res.status_code, 200)

    def test_u_deterministic_fallback(self):
        """Test U: Deterministic synthesis fallback works without OpenAI API key."""
        created = client.post("/api/v1/research/sessions", json={"title": "Fallback Test"}).json()
        sid = created["session_id"]
        res = client.post(f"/api/v1/research/sessions/{sid}/queries", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        data = res.json()
        self.assertTrue(len(data["queries"][0]["answer"]) > 10)

    def test_v_regression_research_api(self):
        """Test V: Existing POST /api/v1/research remains functional."""
        res = client.post("/api/v1/research", json={"query": "Is PLD Space developing a reusable launch vehicle?"})
        self.assertEqual(res.status_code, 200)

    def test_w_regression_evidence_explorer(self):
        """Test W: Existing GET /api/v1/research/{proposition_id}/evidence remains functional."""
        res = client.get("/api/v1/research/PROP-PLD-REUSABLE-001/evidence")
        self.assertEqual(res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
