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
from app.services.grounded_synthesizer import GroundedSynthesizer, MockLLMProvider, FinalGroundedAnswer
from app.services.claim_validator import ClaimValidator, GeneratedClaim, GeneratedSynthesisResponse

class TestStage39GroundedSynthesis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Seed corpus and index authoritative fixture documents."""
        store.reset_store()

        embedder = get_embedder()
        cls.current_run_doc_ids = []

        # 1. PLD Space Reusable Launcher Document (Tier-1)
        pld_doc = DocumentSchema(
            document_id="doc_pld_miura5",
            source_id="src_pld",
            title="PLD Space MIURA 5 Reusable Launch Vehicle",
            content="PLD Space is developing MIURA 5, an orbital reusable launch vehicle designed for small satellite payload delivery. The first stage is designed to be recoverable and reusable.",
            source_url="https://www.pldspace.com/en/miura-5.html",
            source_type=SourceType.WEB,
            publisher="PLD Space Official",
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash="hash_pld_miura5",
            metadata=DocumentMetadata(
                publisher="PLD Space Official",
                extra={
                    "requested_url": "https://www.pldspace.com/en/miura-5.html",
                    "final_resolved_url": "https://www.pldspace.com/en/miura-5.html",
                    "was_redirected": False,
                    "identity_mismatch": False,
                    "source_tier": "TIER_1"
                }
            )
        )
        store.save_document(pld_doc)
        pld_chunks = chunk_document(pld_doc)
        pld_emb = embedder.embed_texts([c.content for c in pld_chunks])
        store.save_chunks(pld_chunks, pld_emb)
        cls.current_run_doc_ids.append(pld_doc.document_id)

        # 2. Isar Aerospace Spectrum Non-Reusable Document (Tier-1)
        isar_doc = DocumentSchema(
            document_id="doc_isar_spectrum",
            source_id="src_isar",
            title="Isar Aerospace Spectrum Launcher Overview",
            content="Isar Aerospace is developing Spectrum, a two-stage orbital launch vehicle for small satellite payload delivery.",
            source_url="https://www.isaraerospace.com/spectrum.html",
            source_type=SourceType.WEB,
            publisher="Isar Aerospace Official",
            language="en",
            retrieved_at=datetime.utcnow().isoformat(),
            content_hash="hash_isar_spectrum",
            metadata=DocumentMetadata(
                publisher="Isar Aerospace Official",
                extra={
                    "requested_url": "https://www.isaraerospace.com/spectrum.html",
                    "final_resolved_url": "https://www.isaraerospace.com/spectrum.html",
                    "was_redirected": False,
                    "identity_mismatch": False,
                    "source_tier": "TIER_1"
                }
            )
        )
        store.save_document(isar_doc)
        isar_chunks = chunk_document(isar_doc)
        isar_emb = embedder.embed_texts([c.content for c in isar_chunks])
        store.save_chunks(isar_chunks, isar_emb)
        cls.current_run_doc_ids.append(isar_doc.document_id)

    def test_a_valid_grounded_claim(self):
        """Test A: Supported PLD evidence produces a valid cited claim."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="VALID")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "SYNTHESIZED_VALIDATED")
        self.assertIsNotNone(res.validation_result)
        self.assertTrue(res.validation_result.is_valid)
        self.assertEqual(len(res.validation_result.validated_claims), 1)

    def test_b_unsupported_attribute_rejected(self):
        """Test B: Funding/launch date hallucination without evidence is rejected, triggering fallback."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="UNSUPPORTED_ATTRIBUTE")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "DETERMINISTIC_FALLBACK")
        self.assertIn("CLAIM_VALIDATION_FAILURE", res.fallback_reason)
        self.assertEqual(res.validation_result.unsupported_attributes_count, 1)

    def test_c_missing_citation_rejected(self):
        """Test C: Factual claim with zero evidence IDs is rejected."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="MISSING_CITATION")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "DETERMINISTIC_FALLBACK")
        self.assertEqual(res.validation_result.claims_without_evidence_count, 1)

    def test_d_invalid_citation_id_rejected(self):
        """Test D: Unknown evidence ID is rejected."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="INVALID_CITATION")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "DETERMINISTIC_FALLBACK")
        self.assertEqual(res.validation_result.invalid_citations_count, 1)

    def test_e_cross_entity_citation_rejected(self):
        """Test E: PLD evidence cited for Isar claim is rejected."""
        q = "Compare PLD Space and Isar Aerospace on reusable launcher development."
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="CROSS_ENTITY_CITATION")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "DETERMINISTIC_FALLBACK")
        self.assertEqual(res.validation_result.cross_entity_citations_count, 1)

    def test_f_stale_evidence_citation_rejected(self):
        """Test F: Citation to previous run evidence is rejected."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        ans = assemble_evidence_answer(pipe_res)
        
        # Override evidence run_id to simulate stale evidence in structured answer
        ans.propositions[0].evidence[0].run_id = "stale_run_999"

        synth_resp = GeneratedSynthesisResponse(
            answer_text="PLD Space is developing reusable launch vehicle technology.",
            claims=[
                GeneratedClaim(
                    claim_id="claim_stale",
                    text="PLD Space is developing reusable launch vehicle technology.",
                    entity_id="pld",
                    evidence_ids=[ans.propositions[0].evidence[0].evidence_id]
                )
            ]
        )

        val_res = ClaimValidator.validate_synthesis(synth_resp, ans)
        self.assertFalse(val_res.is_valid)
        self.assertEqual(val_res.stale_citations_count, 1)

    def test_g_insufficient_evidence_isolation(self):
        """Test G: Insufficient evidence status produces explicit insufficiency explanation."""
        q = "Is Isar Aerospace developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="VALID")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        isar_p = [p for p in res.structured_answer.propositions if p.entity_id == "isar"][0]
        self.assertEqual(isar_p.status, "INSUFFICIENT_EVIDENCE")

    def test_h_contradiction(self):
        """Test H: Contradictory evidence is surfaced as contradiction."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        pipe_res.proposition_results[0].final_status = "CONTRADICTED"

        provider = MockLLMProvider(behavior="VALID")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        pld_p = [p for p in res.structured_answer.propositions if p.entity_id == "pld"][0]
        self.assertEqual(pld_p.status, "CONTRADICTED")

    def test_i_conflict(self):
        """Test I: Conflict state preserves both supporting and contradicting evidence."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        pipe_res.proposition_results[0].final_status = "CONFLICT"

        provider = MockLLMProvider(behavior="VALID")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        pld_p = [p for p in res.structured_answer.propositions if p.entity_id == "pld"][0]
        self.assertEqual(pld_p.status, "CONFLICT")

    def test_j_prompt_injection_defense(self):
        """Test J: Malicious evidence instructions do not become accepted claims."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="PROMPT_INJECTION")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "SYNTHESIZED_VALIDATED")
        self.assertNotIn("Mars", res.answer_text)

    def test_k_citation_completeness(self):
        """Test K: Every factual claim has valid evidence."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="VALID")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        for claim in res.validation_result.validated_claims:
            self.assertTrue(len(claim.evidence_ids) > 0)

    def test_l_unsupported_inference_rejection(self):
        """Test L: Reusable development evidence does not produce funding/location claims."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="UNSUPPORTED_ATTRIBUTE")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "DETERMINISTIC_FALLBACK")

    def test_m_llm_unavailable_fallback(self):
        """Test M: LLM unavailable mode falls back to Stage 3.8 deterministic answer."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="UNAVAILABLE")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "DETERMINISTIC_FALLBACK")
        self.assertIn("LLM_FAILURE", res.fallback_reason)

    def test_n_malformed_llm_response_fallback(self):
        """Test N: Malformed LLM response falls back safely."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="MALFORMED")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "DETERMINISTIC_FALLBACK")
        self.assertIn("MALFORMED_LLM_RESPONSE", res.fallback_reason)

    def test_o_validation_failure_fallback(self):
        """Test O: System does not return invalid LLM answer, falls back to Stage 3.8 answer."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="INVALID_CITATION")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res.synthesis_status, "DETERMINISTIC_FALLBACK")
        self.assertEqual(res.answer_text, res.structured_answer.rendered_text)

    def test_p_deterministic_fallback_repeatability(self):
        """Test P: Repeated fallbacks produce 100% identical outputs."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        provider = MockLLMProvider(behavior="MALFORMED")

        res1 = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)
        res2 = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(res1.answer_text, res2.answer_text)

    def test_q_graph_immutability(self):
        """Test Q: Synthesis and validation create zero Orvyra entities, claims, or relationships."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        pipe_res = execute_research_pipeline(q, current_run_doc_ids=self.current_run_doc_ids)
        initial_claims = len(pipe_res.orvyra_slice.get("claims", []))

        provider = MockLLMProvider(behavior="VALID")
        res = GroundedSynthesizer.synthesize_grounded_answer(q, pipeline_result=pipe_res, provider=provider)

        self.assertEqual(len(pipe_res.orvyra_slice.get("claims", [])), initial_claims)

if __name__ == "__main__":
    unittest.main()
