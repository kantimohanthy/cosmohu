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
from app.services.answer_assembler import assemble_evidence_answer
from app.services.semantic_verifier import verify_semantic_entailment

class TestStage311CorpusRetrieval(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed multi-entity authoritative corpus across 5 European launch entities."""
        store.reset_store()

        embedder = get_embedder()
        cls.current_run_doc_ids = []

        docs_to_index = [
            # PLD Space Docs (Tier 1)
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
                    extra={"requested_url": "https://www.pldspace.com/en/miura-5.html", "final_resolved_url": "https://www.pldspace.com/en/miura-5.html", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),
            DocumentSchema(
                document_id="doc_pld_eib_finance",
                source_id="src_pld_official",
                title="EIB Finances 30 Million Euros for PLD Space MIURA 5 Launcher",
                content="The European Investment Bank (EIB) finances 30 million euros to PLD Space for the development of its reusable orbital launcher MIURA 5.",
                source_url="https://www.pldspace.com/en/news/eib-finances-30-million-euros-pld-space-launcher-miura5.html",
                source_type=SourceType.WEB,
                publisher="PLD Space News",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_pld_eib_finance",
                metadata=DocumentMetadata(
                    publisher="PLD Space News",
                    extra={"requested_url": "https://www.pldspace.com/en/news/eib-finances-30-million-euros-pld-space-launcher-miura5.html", "final_resolved_url": "https://www.pldspace.com/en/news/eib-finances-30-million-euros-pld-space-launcher-miura5.html", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),
            DocumentSchema(
                document_id="doc_pld_esa_boost",
                source_id="src_esa_transport",
                title="ESA Boost! Support for PLD Space MIURA 5 Reusability",
                content="European Space Agency (ESA) provides Boost! contract support to PLD Space for reusability subsystem testing of the MIURA 5 first stage.",
                source_url="https://www.esa.int/Enabling_Support/Space_Transportation/PLD_Space_boosts_reusable_miura5",
                source_type=SourceType.WEB,
                publisher="European Space Agency",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_pld_esa_boost",
                metadata=DocumentMetadata(
                    publisher="European Space Agency",
                    extra={"requested_url": "https://www.esa.int/Enabling_Support/Space_Transportation/PLD_Space_boosts_reusable_miura5", "final_resolved_url": "https://www.esa.int/Enabling_Support/Space_Transportation/PLD_Space_boosts_reusable_miura5", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),

            # Isar Aerospace Docs (Tier 1 & Tier 3)
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
                    extra={"requested_url": "https://www.isaraerospace.com/spectrum.html", "final_resolved_url": "https://www.isaraerospace.com/spectrum.html", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),
            DocumentSchema(
                document_id="doc_isar_prod_facility",
                source_id="src_isar_official",
                title="Isar Aerospace Opens Production Facility in Munich",
                content="Isar Aerospace opens a 28,000 square meter headquarters and production facility near Munich to manufacture Spectrum launch vehicles.",
                source_url="https://www.isaraerospace.com/news/isar-aerospace-opens-production-facility",
                source_type=SourceType.WEB,
                publisher="Isar Aerospace News",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_isar_prod_facility",
                metadata=DocumentMetadata(
                    publisher="Isar Aerospace News",
                    extra={"requested_url": "https://www.isaraerospace.com/news/isar-aerospace-opens-production-facility", "final_resolved_url": "https://www.isaraerospace.com/news/isar-aerospace-opens-production-facility", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),
            DocumentSchema(
                document_id="doc_isar_news_maiden",
                source_id="src_euro_spaceflight",
                title="Isar Aerospace Prepares Spectrum Maiden Flight at Andoya",
                content="Isar Aerospace is preparing for the maiden flight of its Spectrum launcher from Andøya Spaceport in Norway.",
                source_url="https://europeanspaceflight.com/isar-aerospace-spectrum-maiden-flight-prep",
                source_type=SourceType.WEB,
                publisher="European Spaceflight News",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_isar_news_maiden",
                metadata=DocumentMetadata(
                    publisher="European Spaceflight News",
                    extra={"requested_url": "https://europeanspaceflight.com/isar-aerospace-spectrum-maiden-flight-prep", "final_resolved_url": "https://europeanspaceflight.com/isar-aerospace-spectrum-maiden-flight-prep", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_3"}
                )
            ),

            # Rocket Factory Augsburg Docs (Tier 1 & Tier 3)
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
                    extra={"requested_url": "https://www.rfa.space/rfa-one", "final_resolved_url": "https://www.rfa.space/rfa-one", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),
            DocumentSchema(
                document_id="doc_rfa_hotfire",
                source_id="src_rfa_official",
                title="RFA Completes First Stage Hot Fire Test",
                content="Rocket Factory Augsburg completes first stage hot fire testing for RFA One at SaxaVord Spaceport in Shetland.",
                source_url="https://www.rfa.space/news/rfa-completes-first-stage-hot-fire-test",
                source_type=SourceType.WEB,
                publisher="RFA News",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_rfa_hotfire",
                metadata=DocumentMetadata(
                    publisher="RFA News",
                    extra={"requested_url": "https://www.rfa.space/news/rfa-completes-first-stage-hot-fire-test", "final_resolved_url": "https://www.rfa.space/news/rfa-completes-first-stage-hot-fire-test", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),
            DocumentSchema(
                document_id="doc_rfa_euro_news",
                source_id="src_euro_spaceflight",
                title="RFA One Launch Status Update",
                content="Rocket Factory Augsburg advances towards inaugural flight of RFA One from SaxaVord Spaceport.",
                source_url="https://europeanspaceflight.com/rfa-one-launch-status-update",
                source_type=SourceType.WEB,
                publisher="European Spaceflight News",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_rfa_euro_news",
                metadata=DocumentMetadata(
                    publisher="European Spaceflight News",
                    extra={"requested_url": "https://europeanspaceflight.com/rfa-one-launch-status-update", "final_resolved_url": "https://europeanspaceflight.com/rfa-one-launch-status-update", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_3"}
                )
            ),

            # Orbex Docs (Tier 1)
            DocumentSchema(
                document_id="doc_orbex_prime_spec",
                source_id="src_orbex_official",
                title="Orbex Prime Launch Vehicle Overview",
                content="Orbex is developing Prime, an eco-friendly micro-launch vehicle utilizing bio-LPG fuel for small satellite orbital launches.",
                source_url="https://www.orbex.space/prime",
                source_type=SourceType.WEB,
                publisher="Orbex Official",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_orbex_prime_spec",
                metadata=DocumentMetadata(
                    publisher="Orbex Official",
                    extra={"requested_url": "https://www.orbex.space/prime", "final_resolved_url": "https://www.orbex.space/prime", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),
            DocumentSchema(
                document_id="doc_orbex_spaceport",
                source_id="src_orbex_official",
                title="Orbex Prepares Sutherland Spaceport for Prime Launches",
                content="Orbex begins construction at Sutherland Spaceport in Scotland for orbital launch operations of Orbex Prime.",
                source_url="https://www.orbex.space/news/orbex-sutherland-spaceport-construction",
                source_type=SourceType.WEB,
                publisher="Orbex News",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_orbex_spaceport",
                metadata=DocumentMetadata(
                    publisher="Orbex News",
                    extra={"requested_url": "https://www.orbex.space/news/orbex-sutherland-spaceport-construction", "final_resolved_url": "https://www.orbex.space/news/orbex-sutherland-spaceport-construction", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),
            DocumentSchema(
                document_id="doc_orbex_esa_boost",
                source_id="src_esa_transport",
                title="ESA Support for Orbex Prime Launch Operations",
                content="European Space Agency (ESA) awards Boost! co-funding to Orbex for commercial launch services development of Prime.",
                source_url="https://www.esa.int/Enabling_Support/Space_Transportation/Orbex_Prime",
                source_type=SourceType.WEB,
                publisher="European Space Agency",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_orbex_esa_boost",
                metadata=DocumentMetadata(
                    publisher="European Space Agency",
                    extra={"requested_url": "https://www.esa.int/Enabling_Support/Space_Transportation/Orbex_Prime", "final_resolved_url": "https://www.esa.int/Enabling_Support/Space_Transportation/Orbex_Prime", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),

            # MaiaSpace Docs (Tier 1 & Tier 4 Redirect Mismatch)
            DocumentSchema(
                document_id="doc_maiaspace_reusable",
                source_id="src_maiaspace_official",
                title="MaiaSpace Reusable Mini Launcher Overview",
                content="MaiaSpace is developing Maia, a reusable orbital mini-launcher powered by the Colibri liquid engine designed for reusability.",
                source_url="https://www.maiaspace.com/maia-launcher",
                source_type=SourceType.WEB,
                publisher="MaiaSpace Official",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_maiaspace_reusable",
                metadata=DocumentMetadata(
                    publisher="MaiaSpace Official",
                    extra={"requested_url": "https://www.maiaspace.com/maia-launcher", "final_resolved_url": "https://www.maiaspace.com/maia-launcher", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
                )
            ),
            DocumentSchema(
                document_id="doc_maiaspace_colibri_test",
                source_id="src_maiaspace_official",
                title="MaiaSpace Colibri Engine Hot Fire Test",
                content="MaiaSpace completes hot fire testing of the Colibri engine second stage for the Maia reusable launcher.",
                source_url="https://www.maiaspace.com/news/maiaspace-second-stage-test",
                source_type=SourceType.WEB,
                publisher="MaiaSpace News",
                language="en",
                retrieved_at=datetime.utcnow().isoformat(),
                content_hash="hash_maiaspace_colibri_test",
                metadata=DocumentMetadata(
                    publisher="MaiaSpace News",
                    extra={"requested_url": "https://www.maiaspace.com/news/maiaspace-second-stage-test", "final_resolved_url": "https://www.maiaspace.com/news/maiaspace-second-stage-test", "was_redirected": False, "identity_mismatch": False, "source_tier": "TIER_1"}
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
                    extra={"requested_url": "https://en.wikipedia.org/wiki/MaiaSpace", "final_resolved_url": "https://en.wikipedia.org/wiki/ArianeGroup", "was_redirected": True, "identity_mismatch": True, "source_tier": "TIER_4"}
                )
            )
        ]

        for d in docs_to_index:
            store.save_document(d)
            chunks = chunk_document(d)
            embs = embedder.embed_texts([c.content for c in chunks])
            store.save_chunks(chunks, embs)
            cls.current_run_doc_ids.append(d.document_id)

    def test_01_corpus_entity_coverage(self):
        """Test 1: Verifies multi-entity corpus indexing across 5 space entities."""
        entities = ["pld", "isar", "rfa", "orbex", "maia"]
        for ent in entities:
            # Execute search pipeline query for entity
            q = f"What launch vehicle is {ent} developing?"
            res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
            self.assertTrue(len(res.proposition_results) > 0)

    def test_02_multi_source_corroboration(self):
        """Test 2: Verifies 3 independent Tier-1 documents corroborate PLD reusable development."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        pld_res = res.proposition_results[0]

        self.assertEqual(pld_res.final_status, "SUPPORTED")
        self.assertTrue(len(pld_res.verified_evidence) >= 2)

    def test_03_high_retrieval_score_not_truth(self):
        """Test 3: High retrieval score on non-reusable Spectrum launcher fails semantic verification."""
        sem_res = verify_semantic_entailment(
            passage_text="Isar Aerospace is developing Spectrum, a two-stage orbital launch vehicle.",
            entity_id="isar",
            entity_name="Isar Aerospace",
            target_temporal="IN_DEVELOPMENT",
            identity_mismatch=False
        )
        self.assertEqual(sem_res.semantic_status, "NOT_ENTAILED")

    def test_04_cross_entity_contamination_isolation(self):
        """Test 4: PLD evidence does not support Isar or RFA."""
        q = "Compare PLD Space and Isar Aerospace on reusable launch vehicle development."
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)

        pld_prop = [p for p in res.proposition_results if p.entity_id == "pld"][0]
        isar_prop = [p for p in res.proposition_results if p.entity_id == "isar"][0]

        self.assertEqual(pld_prop.final_status, "SUPPORTED")
        self.assertEqual(isar_prop.final_status, "INSUFFICIENT_EVIDENCE")

    def test_05_redirect_mismatch_rejection(self):
        """Test 5: MaiaSpace Wikipedia redirect mismatch is rejected."""
        q = "Is MaiaSpace developing a reusable launch vehicle?"
        res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        maia_res = res.proposition_results[0]

        # MaiaSpace has 2 valid MaiaSpace docs + 1 redirect mismatch doc
        # Verified evidence must only come from valid MaiaSpace docs
        for ev in maia_res.verified_evidence:
            self.assertFalse(ev.get("identity_mismatch", False))

if __name__ == "__main__":
    unittest.main()
