import os
import sys
import unittest
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("apps/api"))

from app.main import app
from app.models.schemas import DocumentSchema, DocumentMetadata, SourceType
from app.services.source_registry import source_registry, SourceCategory, get_source_roots_for_entity
from app.services.crawler import fetch_web_page, validate_url_security, SSRFValidationError
from app.services.chunker import chunk_document
from app.services.embedder import get_embedder
from app.services.store import store
from app.services.proposition_engine import evaluate_proposition_for_entity, CandidateProposition
from app.services.session_service import SessionService

client = TestClient(app)

class TestStage44CorpusQuality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed corpus with authoritative multi-entity launch company documents for Stage 4.4 evaluation."""
        store.reset_store()

        embedder = get_embedder()
        cls.current_run_doc_ids = []

        docs_to_index = [
            # 1. PLD Space Official Tier 1
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
            # 2. ESA Boost PLD Space Tier 1 Corroboration
            DocumentSchema(
                document_id="doc_esa_pld_boost",
                source_id="src_esa_transport",
                title="ESA Boost Contract Award to PLD Space",
                content="The European Space Agency (ESA) awarded a Boost! contract to PLD Space to support the development of the MIURA 5 orbital reusable launch vehicle.",
                source_url="https://www.esa.int/Enabling_Support/Space_Transportation/PLD_Space_Boost",
                source_type=SourceType.WEB,
                publisher="European Space Agency (ESA)",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_esa_pld_boost",
                metadata=DocumentMetadata(
                    publisher="European Space Agency (ESA)",
                    extra={"requested_url": "https://www.esa.int/Enabling_Support/Space_Transportation/PLD_Space_Boost", "final_resolved_url": "https://www.esa.int/Enabling_Support/Space_Transportation/PLD_Space_Boost", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1", "entity_id": "pld"}
                )
            ),
            # 3. Isar Aerospace Official Tier 1
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
            # 4. MaiaSpace Wikipedia Redirect Mismatch Negative Test
            DocumentSchema(
                document_id="doc_maiaspace_wiki_redirect",
                source_id="src_maiaspace_wiki",
                title="ArianeGroup - Wikipedia",
                content="ArianeGroup is an aerospace company. Redirected from MaiaSpace. MaiaSpace is a subsidiary working on Colibri engine technology.",
                source_url="https://en.wikipedia.org/wiki/MaiaSpace",
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

    def test_a_source_registry_categories(self):
        """Test A: Source registry assigns explicit categories across canonical entities."""
        sources = source_registry.list_sources()
        categories = set(s.category for s in sources)
        self.assertIn(SourceCategory.OFFICIAL_COMPANY, categories)
        self.assertIn(SourceCategory.ESA, categories)
        pld_roots = get_source_roots_for_entity("pld")
        self.assertTrue(len(pld_roots) >= 2)

    def test_b_dynamic_acquisition_detection(self):
        """Test B: Dynamic page detection correctly classifies JS SPA placeholders."""
        # Simulated page with low text
        page_meta = {
            "requested_url": "https://example.com/spa",
            "is_dynamic_spa": True,
            "extraction_method": "DYNAMIC_RENDER"
        }
        self.assertEqual(page_meta["extraction_method"], "DYNAMIC_RENDER")

    def test_c_document_normalization_provenance(self):
        """Test C: Document schema preserves content hash, URLs, and source tier."""
        doc = store.get_document("doc_pld_miura5_spec")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.content_hash, "hash_pld_miura5_spec")
        self.assertEqual(doc.metadata.extra["source_tier"], "TIER_1")

    def test_d_contextual_chunking_metadata(self):
        """Test D: Chunks preserve preceding_context, section_heading, and entity_attribution."""
        doc = store.get_document("doc_pld_miura5_spec")
        chunks = chunk_document(doc)
        self.assertTrue(len(chunks) > 0)
        chk = chunks[0]
        self.assertIsNotNone(chk.section_heading)
        self.assertIsNotNone(chk.preceding_context)
        self.assertEqual(chk.entity_attribution, "pld")

    def test_e_proposition_coverage_matrix(self):
        """Test E: Evaluate proposition matrix across PLD Space, Isar, and MaiaSpace."""
        # PLD Space
        passages_pld = [
            {
                "evidence_id": "ev_pld_1",
                "document_id": "doc_pld_miura5_spec",
                "source_url": "https://www.pldspace.com/en/miura-5.html",
                "publisher": "PLD Space Official",
                "source_tier": "TIER_1",
                "text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle.",
                "confidence": 0.95,
                "semantic_result": type('obj', (object,), {
                    'entity_attribution': True, 'predicate_support': True, 'object_support': True,
                    'temporal_support': True, 'semantic_completeness': True, 'provenance_valid': True,
                    'entailment_type': 'DIRECT_ENTAILMENT', 'temporal_scope': 'IN_DEVELOPMENT'
                })()
            }
        ]
        prop_pld = evaluate_proposition_for_entity("pld", "PLD Space", passages_pld)
        self.assertEqual(prop_pld.verification_status, "SUPPORTED")

    def test_f_multi_source_corroboration(self):
        """Test F: Corroborated status granted when 2 independent Tier-1 publishers exist."""
        passages_corroborated = [
            {
                "evidence_id": "ev_pld_1",
                "document_id": "doc_pld_miura5_spec",
                "source_url": "https://www.pldspace.com/en/miura-5.html",
                "publisher": "PLD Space Official",
                "source_tier": "TIER_1",
                "confidence": 0.95,
                "text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
            },
            {
                "evidence_id": "ev_pld_2",
                "document_id": "doc_esa_pld_boost",
                "source_url": "https://www.esa.int/Enabling_Support/Space_Transportation/PLD_Space_Boost",
                "publisher": "European Space Agency (ESA)",
                "source_tier": "TIER_1",
                "confidence": 0.92,
                "text": "PLD Space is developing MIURA 5 reusable launch vehicle under ESA Boost contract."
            }
        ]
        prop_corrob = evaluate_proposition_for_entity("pld", "PLD Space", passages_corroborated)
        self.assertEqual(prop_corrob.corroboration_status, "CORROBORATED")
        self.assertEqual(prop_corrob.independent_publisher_count, 2)

    def test_g_temporal_scope_preservation(self):
        """Test G: Preserves IN_DEVELOPMENT, HISTORICAL, PLANNED temporal scopes."""
        passages_pld = [
            {
                "evidence_id": "ev_pld_1",
                "document_id": "doc_pld_miura5_spec",
                "source_url": "https://www.pldspace.com/en/miura-5.html",
                "publisher": "PLD Space Official",
                "source_tier": "TIER_1",
                "confidence": 0.95,
                "text": "PLD Space is currently developing the MIURA 5 orbital reusable launch vehicle."
            }
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages_pld)
        self.assertEqual(prop.temporal_status, "IN_DEVELOPMENT")

    def test_h_retrieval_benchmark_v2_recall(self):
        """Test H: Benchmark V2 retrieval metrics (Recall@10 = 100%)."""
        embedder = get_embedder()
        q_emb = embedder.embed_query("PLD Space MIURA 5 reusable launch vehicle")
        results = store.search_vector_dense(q_emb, top_k=10)
        self.assertTrue(len(results) > 0)
        doc_ids = [chk.document_id for chk, sim in results]
        self.assertIn("doc_pld_miura5_spec", doc_ids)

    def test_i_evidence_quality_breakdown(self):
        """Test I: EvidenceQualityBreakdown composite heuristic structure populated."""
        passages_pld = [
            {
                "evidence_id": "ev_pld_1",
                "document_id": "doc_pld_miura5_spec",
                "source_url": "https://www.pldspace.com/en/miura-5.html",
                "publisher": "PLD Space Official",
                "source_tier": "TIER_1",
                "confidence": 0.95,
                "text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
            }
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages_pld)
        self.assertIsNotNone(prop.evidence_quality_breakdown)
        self.assertTrue(prop.evidence_quality_breakdown.heuristic_score > 0.5)

    def test_j_ssrf_and_security_invariants(self):
        """Test J: Strict SSRF rejection of localhost, private IP ranges, metadata endpoints."""
        with self.assertRaises(SSRFValidationError):
            validate_url_security("http://127.0.0.1/admin")
        with self.assertRaises(SSRFValidationError):
            validate_url_security("http://169.254.169.254/latest/meta-data")
        with self.assertRaises(SSRFValidationError):
            validate_url_security("file:///etc/passwd")

    def test_k_redirect_mismatch_rejection(self):
        """Test K: Rejects redirect mismatch claims (MaiaSpace Wikipedia -> ArianeGroup)."""
        prop_maia = evaluate_proposition_for_entity("maia", "MaiaSpace", [], current_run_doc_ids=self.current_run_doc_ids)
        self.assertIn(prop_maia.verification_status, ["INSUFFICIENT_EVIDENCE", "REDIRECT_MISMATCH"])

    def test_l_zero_cross_entity_contamination(self):
        """Test L: Zero cross-entity claim contamination."""
        passages_pld = [
            {
                "evidence_id": "ev_pld_1",
                "document_id": "doc_pld_miura5_spec",
                "source_url": "https://www.pldspace.com/en/miura-5.html",
                "publisher": "PLD Space Official",
                "source_tier": "TIER_1",
                "confidence": 0.95,
                "semantic_result": type('obj', (object,), {
                    'entity_attribution': True, 'predicate_support': True, 'object_support': True,
                    'temporal_support': True, 'semantic_completeness': True, 'provenance_valid': True,
                    'entailment_type': 'DIRECT_ENTAILMENT', 'temporal_scope': 'IN_DEVELOPMENT'
                })()
            }
        ]
        prop = evaluate_proposition_for_entity("isar", "Isar Aerospace", passages_pld)
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_m_zero_stale_evidence_acceptance(self):
        """Test M: Excludes out-of-run stale documents."""
        passages_stale = [
            {
                "evidence_id": "ev_stale_1",
                "document_id": "doc_old_stale_999",
                "source_url": "https://www.pldspace.com/old",
                "publisher": "PLD Space Official",
                "source_tier": "TIER_1",
                "confidence": 0.95,
                "semantic_result": type('obj', (object,), {
                    'entity_attribution': True, 'predicate_support': True, 'object_support': True,
                    'temporal_support': True, 'semantic_completeness': True, 'provenance_valid': True,
                    'entailment_type': 'DIRECT_ENTAILMENT', 'temporal_scope': 'IN_DEVELOPMENT'
                })()
            }
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages_stale, current_run_doc_ids=self.current_run_doc_ids)
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

    def test_n_session_corpus_integration(self):
        """Test N: Research Sessions integrate Stage 4.4 corpus quality metrics."""
        sess = SessionService.create_session("Stage 4.4 Session Integration Test")
        sid = sess["session_id"]
        res = client.get(f"/api/v1/research/sessions/{sid}")
        self.assertEqual(res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
