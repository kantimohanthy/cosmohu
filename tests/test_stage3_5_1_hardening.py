import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.semantic_verifier import verify_semantic_entailment, SemanticVerificationResult
from app.services.proposition_engine import evaluate_proposition_for_entity, CandidateProposition
from app.services.orvyra_adapter import OrvyraAdapter, generate_deterministic_evidence_id
from app.models.schemas import EvidencePassage

class TestStage351SemanticEntailmentHardening(unittest.TestCase):

    # =========================================================================
    # 1. 10 ADVERSARIAL NEGATIVE FIXTURES (Fixtures A - J)
    # =========================================================================

    def test_fixture_a_generic_statement(self):
        """Fixture A: Generic statement -> NOT_ENTAILED (Missing Entity Attribution)."""
        text = "Reusable launch vehicles are becoming increasingly important in Europe."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertFalse(res.entity_attribution)
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertEqual(res.failure_component, "entity")

    def test_fixture_b_entity_and_reusable_no_development(self):
        """Fixture B: Entity + reusable, but operational/no development -> NOT_ENTAILED."""
        text = "PLD Space operates a reusable launch vehicle."
        res = verify_semantic_entailment(text, "pld", "PLD Space", target_temporal="IN_DEVELOPMENT")
        
        self.assertTrue(res.entity_attribution)
        self.assertFalse(res.predicate_support)
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertEqual(res.failure_component, "predicate")

    def test_fixture_c_entity_and_development_no_reusable(self):
        """Fixture C: Entity + development, but no reusable property -> NOT_ENTAILED."""
        text = "PLD Space is developing a new orbital launch vehicle."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertTrue(res.entity_attribution)
        self.assertTrue(res.predicate_support)
        self.assertFalse(res.object_support)
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertEqual(res.failure_component, "object")

    def test_fixture_d_reusable_vehicle_historical(self):
        """Fixture D: Reusable vehicle, but historical concept -> NOT_ENTAILED."""
        text = "PLD Space investigated reusable launch vehicle concepts in 2018."
        res = verify_semantic_entailment(text, "pld", "PLD Space", target_temporal="IN_DEVELOPMENT")
        
        self.assertTrue(res.entity_attribution)
        self.assertTrue(res.predicate_support)
        self.assertTrue(res.object_support)
        self.assertFalse(res.temporal_support)
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertEqual(res.failure_component, "temporal_scope")

    def test_fixture_e_reusable_vehicle_cancelled(self):
        """Fixture E: Reusable vehicle, cancelled program -> NOT_ENTAILED."""
        text = "PLD Space developed the reusable Miura 5 concept before cancelling the program."
        res = verify_semantic_entailment(text, "pld", "PLD Space", target_temporal="IN_DEVELOPMENT")
        
        self.assertFalse(res.temporal_support)
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")
        self.assertEqual(res.failure_component, "temporal_scope")

    def test_fixture_f_explicit_negation(self):
        """Fixture F: Explicit negation -> CONTRADICTED."""
        text = "PLD Space is not developing a reusable launch vehicle."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertTrue(res.is_contradiction)
        self.assertEqual(res.semantic_status, "CONTRADICTED")
        self.assertEqual(res.failure_component, "contradiction")

    def test_fixture_g_mixed_statement_third_party_predicate(self):
        """Fixture G: Mixed statement where reusable development belongs to another company -> NOT_ENTAILED."""
        text = "PLD Space develops launch vehicles. Reusable launch vehicles are being developed by another European company."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertFalse(res.predicate_support)
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")

    def test_fixture_h_keyword_collision_component_supplier(self):
        """Fixture H: Keyword collision where entity is component supplier -> NOT_ENTAILED."""
        text = "PLD Space provides components used by companies developing reusable launch vehicles."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertFalse(res.predicate_support)
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")

    def test_fixture_i_property_inheritance_trap(self):
        """Fixture I: Property inheritance trap without entity development predicate -> NOT_ENTAILED."""
        text = "Miura 5 is reusable. PLD Space has announced the vehicle."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertFalse(res.predicate_support)
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")

    def test_fixture_j_contradiction_plus_positive_keyword(self):
        """Fixture J: Positive keyword with explicit non-reusable assertion -> CONTRADICTED."""
        text = "PLD Space is developing Miura 5, but the vehicle is explicitly described as expendable and non-reusable."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertTrue(res.is_contradiction)
        self.assertEqual(res.semantic_status, "CONTRADICTED")

    # =========================================================================
    # 2. 3 POSITIVE ENTAILMENT FIXTURES
    # =========================================================================

    def test_positive_entailment_1(self):
        """Positive 1: Canonical phrasing -> ENTAILED & 5-Dimension PASS."""
        text = "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertTrue(res.entity_attribution)
        self.assertTrue(res.predicate_support)
        self.assertTrue(res.object_support)
        self.assertTrue(res.temporal_support)
        self.assertTrue(res.semantic_completeness)
        self.assertEqual(res.semantic_status, "ENTAILED")

    def test_positive_entailment_2(self):
        """Positive 2: Alternative phrasing -> ENTAILED & 5-Dimension PASS."""
        text = "Spanish launch provider PLD Space is currently designing and building a recoverable first stage launcher."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertTrue(res.semantic_completeness)
        self.assertEqual(res.semantic_status, "ENTAILED")

    def test_positive_entailment_3(self):
        """Positive 3: R&D manufacturing phrasing -> ENTAILED & 5-Dimension PASS."""
        text = "PLD Space R&D programme is actively manufacturing a reusable launch vehicle for commercial satellite missions."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertTrue(res.semantic_completeness)
        self.assertEqual(res.semantic_status, "ENTAILED")

    # =========================================================================
    # 3. 3 TEMPORAL SCOPE FIXTURES
    # =========================================================================

    def test_temporal_active_in_development(self):
        """Temporal 1: Active IN_DEVELOPMENT -> PASS."""
        text = "PLD Space is under active development of a reusable rocket."
        res = verify_semantic_entailment(text, "pld", "PLD Space", target_temporal="IN_DEVELOPMENT")
        
        self.assertTrue(res.temporal_support)
        self.assertEqual(res.temporal_scope, "IN_DEVELOPMENT")

    def test_temporal_future_planned_scope_mismatch(self):
        """Temporal 2: Future PLANNED status for IN_DEVELOPMENT -> Scope Mismatch."""
        text = "PLD Space plans to develop a reusable launcher in 2030."
        res = verify_semantic_entailment(text, "pld", "PLD Space", target_temporal="OPERATIONAL")
        
        self.assertFalse(res.temporal_support)
        self.assertEqual(res.temporal_scope, "PLANNED")

    def test_temporal_historical_test_scope_mismatch(self):
        """Temporal 3: Historical test status for IN_DEVELOPMENT -> Scope Mismatch."""
        text = "PLD Space conducted suborbital test of reusable tech in 2019."
        res = verify_semantic_entailment(text, "pld", "PLD Space", target_temporal="IN_DEVELOPMENT")
        
        self.assertFalse(res.temporal_support)
        self.assertEqual(res.temporal_scope, "HISTORICAL")

    # =========================================================================
    # 4. 3 CONTRADICTION / CONFLICT FIXTURES
    # =========================================================================

    def test_contradiction_single_explicit_refutation(self):
        """Contradiction 1: Explicit refutation -> CONTRADICTED."""
        text = "PLD Space abandoned development of Miura 5."
        res = verify_semantic_entailment(text, "pld", "PLD Space")
        
        self.assertTrue(res.is_contradiction)
        self.assertEqual(res.semantic_status, "CONTRADICTED")

    def test_conflict_coexisting_evidence(self):
        """Contradiction 2: Coexisting supporting + contradicting passages -> CONFLICT."""
        passages = [
            {"evidence_id": "ev1", "evidence_text": "PLD Space is developing MIURA 5, an orbital reusable launch vehicle.", "document_id": "doc1", "source_url": "https://pld.com"},
            {"evidence_id": "ev2", "evidence_text": "PLD Space abandoned development of Miura 5.", "document_id": "doc2", "source_url": "https://news.com"}
        ]
        prop = evaluate_proposition_for_entity("pld", "PLD Space", passages, current_run_doc_ids=["doc1", "doc2"])
        
        self.assertEqual(prop.verification_status, "CONFLICT")

    def test_contradiction_vehicle_expendable_assertion(self):
        """Contradiction 3: Explicit non-reusable architecture refutation -> CONTRADICTED."""
        text = "Isar Aerospace Spectrum is strictly expendable with no reusable architecture."
        res = verify_semantic_entailment(text, "isar", "Isar Aerospace")
        
        self.assertTrue(res.is_contradiction)
        self.assertEqual(res.semantic_status, "CONTRADICTED")

    # =========================================================================
    # 5. 2 CONTEXT VS FRAGMENT FIXTURES
    # =========================================================================

    def test_context_vs_fragment_insufficient_fragment(self):
        """Context 1: Short header fragment alone is INSUFFICIENT_FRAGMENT."""
        fragment = "Discover Miura Next | PLD Space R&D PROGRAM"
        res = verify_semantic_entailment(fragment, "pld", "PLD Space")
        
        self.assertFalse(res.object_support)
        self.assertEqual(res.semantic_status, "NOT_ENTAILED")

    def test_context_vs_fragment_contextual_entailment(self):
        """Context 2: Short fragment + surrounding chunk context yields CONTEXTUAL_ENTAILMENT."""
        fragment = "Discover Miura Next | PLD Space"
        surrounding_chunk = "Discover Miura Next | PLD Space R&D PROGRAM features recoverable first stage launch vehicle."
        res = verify_semantic_entailment(fragment, "pld", "PLD Space", surrounding_context=surrounding_chunk)
        
        self.assertTrue(res.semantic_completeness)
        self.assertEqual(res.entailment_type, "CONTEXTUAL_ENTAILMENT")

    # =========================================================================
    # 6. 2 ANTI-HARDCODING TESTS
    # =========================================================================

    def test_anti_hardcoding_fictitious_entity(self):
        """Anti-Hardcoding 1: Fictitious entity 'custom_ent' evaluates compositionally without shortcuts."""
        text = "Aether Dynamics is developing Prometheus, an orbital reusable launch vehicle."
        res = verify_semantic_entailment(text, "custom_ent", "Aether Dynamics")
        
        self.assertTrue(res.semantic_completeness)
        self.assertEqual(res.semantic_status, "ENTAILED")

    def test_anti_hardcoding_unknown_rocket_name(self):
        """Anti-Hardcoding 2: Unknown rocket name 'Titan-X' evaluates compositionally without cheats."""
        text = "Vanguard Space is designing and manufacturing Titan-X, a recoverable first stage rocket."
        res = verify_semantic_entailment(text, "vanguard", "Vanguard Space")
        
        self.assertTrue(res.semantic_completeness)
        self.assertEqual(res.semantic_status, "ENTAILED")

    # =========================================================================
    # 7. 2 PROVENANCE INTEGRITY TESTS
    # =========================================================================

    def test_provenance_redirect_mismatch_rejected(self):
        """Provenance 1: Identity redirect mismatch returns INVALID_PROVENANCE & provenance_valid = False."""
        text = "ArianeGroup - Wikipedia (Redirected from MaiaSpace)"
        res = verify_semantic_entailment(text, "maia", "MaiaSpace", identity_mismatch=True)
        
        self.assertFalse(res.provenance_valid)
        self.assertEqual(res.semantic_status, "INVALID_PROVENANCE")

    def test_provenance_stale_document_rejected(self):
        """Provenance 2: Stale document ID outside current run returns INSUFFICIENT_EVIDENCE."""
        text = "PLD Space is developing MIURA 5, an orbital reusable launch vehicle."
        prop = evaluate_proposition_for_entity("pld", "PLD Space", [{"evidence_id": "ev_old", "evidence_text": text, "document_id": "doc_stale_99"}], current_run_doc_ids=["doc_fresh_100"])
        
        self.assertEqual(prop.verification_status, "INSUFFICIENT_EVIDENCE")

if __name__ == "__main__":
    unittest.main()
