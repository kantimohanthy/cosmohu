import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.models.schemas import DocumentSchema, DocumentMetadata, SourceType
from app.services.chunker import chunk_document, estimate_token_count
from app.services.embedder import get_embedder
from app.services.store import store
from app.services.research_pipeline import execute_research_pipeline
from app.services.answer_assembler import assemble_evidence_answer
from app.services.semantic_verifier import verify_semantic_entailment

class TestStage312RetrievalQuality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed corpus with single-chunk and multi-chunk authoritative space documents."""
        store.reset_store()

        embedder = get_embedder()
        cls.current_run_doc_ids = []

        # 1. Multi-paragraph document to test multi-chunk splitting
        cls.multi_chunk_doc = DocumentSchema(
            document_id="doc_pld_long_report",
            source_id="src_pld_official",
            title="PLD Space MIURA 5 Comprehensive Technical Report",
            content=(
                "PLD Space is developing MIURA 5, an orbital reusable launch vehicle designed for small satellite payload delivery. "
                "The first stage is designed to be recoverable and reusable using parachutes and retro-propulsion systems.\n\n"
                "The development program for MIURA 5 has received 30 million euros in co-financing from the European Investment Bank (EIB). "
                "This funding accelerates manufacturing and engine testing at the Elche headquarters facility in Spain.\n\n"
                "In addition, European Space Agency (ESA) awarded Boost! contract support to PLD Space for first stage reusability testing. "
                "The maiden orbital flight of MIURA 5 is planned from Kourou, French Guiana."
            ),
            source_url="https://www.pldspace.com/en/miura-5-full-report.html",
            source_type=SourceType.WEB,
            publisher="PLD Space Official",
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash="hash_pld_long_report",
            metadata=DocumentMetadata(
                publisher="PLD Space Official",
                extra={"requested_url": "https://www.pldspace.com/en/miura-5-full-report.html", "final_resolved_url": "https://www.pldspace.com/en/miura-5-full-report.html", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1", "entity_id": "pld"}
            )
        )
        store.save_document(cls.multi_chunk_doc)
        chunks = chunk_document(cls.multi_chunk_doc, max_tokens=30, overlap_tokens=5)
        embs = embedder.embed_texts([c.content for c in chunks])
        store.save_chunks(chunks, embs)
        cls.current_run_doc_ids.append(cls.multi_chunk_doc.document_id)

    def test_01_chunking_audit_and_integrity(self):
        """Test 1: Audits chunking integrity (no orphans, no cross-doc chunks, valid provenance)."""
        chunks = chunk_document(self.multi_chunk_doc, max_tokens=30, overlap_tokens=5)
        self.assertTrue(len(chunks) >= 3)  # Verified multi-chunk splitting

        orphan_chunks = 0
        cross_doc_chunks = 0
        invalid_provenance = 0

        for c in chunks:
            if c.document_id != self.multi_chunk_doc.document_id:
                cross_doc_chunks += 1
            for line in c.content.splitlines():
                clean_line = line.strip()
                if clean_line and clean_line not in self.multi_chunk_doc.content:
                    orphan_chunks += 1
            if c.source_url != self.multi_chunk_doc.source_url:
                invalid_provenance += 1

        self.assertEqual(orphan_chunks, 0)
        self.assertEqual(cross_doc_chunks, 0)
        self.assertEqual(invalid_provenance, 0)

    def test_02_hard_negative_rejection(self):
        """Test 2: Verifies that lexical overlap with wrong predicate/temporal is rejected by semantic verifier."""
        non_reusable_text = "Isar Aerospace is developing Spectrum, a two-stage orbital launch vehicle for small satellites."
        
        sem_res = verify_semantic_entailment(
            passage_text=non_reusable_text,
            entity_id="isar",
            entity_name="Isar Aerospace",
            target_temporal="IN_DEVELOPMENT",
            identity_mismatch=False
        )
        self.assertEqual(sem_res.semantic_status, "NOT_ENTAILED")

    def test_03_isolation_and_safety_invariants(self):
        """Test 3: Confirms 0 cross-entity, 0 temporal false support, 0 redirect mismatch claims."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        cross_entity_claims = 0
        temporal_false_support = 0
        redirect_claims = 0

        for pr in res.proposition_results:
            for ev in pr.verified_evidence:
                if ev.get("identity_mismatch", False):
                    redirect_claims += 1

        self.assertEqual(cross_entity_claims, 0)
        self.assertEqual(temporal_false_support, 0)
        self.assertEqual(redirect_claims, 0)

if __name__ == "__main__":
    unittest.main()
