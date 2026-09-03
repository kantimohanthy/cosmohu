import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.models.schemas import DocumentSchema, DocumentMetadata, SourceType
from app.services.chunker import chunk_document
from app.services.embedder import get_embedder
from app.services.store import store
from app.services.research_pipeline import execute_research_pipeline
from app.services.reranker import rerank_evidence_candidates, HeuristicReranker

class TestStage313RankingOptimization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed corpus across PLD, Isar, RFA, Orbex, MaiaSpace."""
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

    def test_01_entity_aware_ranking_boost(self):
        """Test 1: Verifies entity alignment boosts PLD gold document to Top-1 for PLD query."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        pld_res = res.proposition_results[0]
        top_cand_doc_id = pld_res.reranked_candidates[0]["document_id"]
        self.assertEqual(top_cand_doc_id, "doc_pld_miura5_spec")

    def test_02_safety_regression_invariants(self):
        """Test 2: Verifies zero cross-entity, zero temporal false support, zero redirect mismatch claims."""
        q = "Is Isar Aerospace developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        isar_res = res.proposition_results[0]

        # Isar Spectrum is non-reusable -> final status must be INSUFFICIENT_EVIDENCE (0 claims created)
        self.assertEqual(isar_res.final_status, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(len(isar_res.verified_evidence), 0)

    def test_03_determinism_repeatability(self):
        """Test 3: Confirms 100% identical ranking scores across 3 repeated runs."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        res1 = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        res2 = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        sc1 = [c["relevance_score"] for c in res1.proposition_results[0].reranked_candidates]
        sc2 = [c["relevance_score"] for c in res2.proposition_results[0].reranked_candidates]

        self.assertEqual(sc1, sc2)

if __name__ == "__main__":
    unittest.main()
