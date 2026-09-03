import os
import sys
import unittest

sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.planner import (
    build_deterministic_query_plan,
    QueryPlan,
    QueryProposition,
    ResolvedEntity
)
from app.services.orvyra_adapter import OrvyraAdapter

class TestStage36QueryPlanner(unittest.TestCase):

    def test_a_single_proposition_query(self):
        """Test A: Single proposition query -> 1 entity, 1 proposition, status UNVERIFIED."""
        q = "Is PLD Space developing a reusable launch vehicle?"
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "SUCCESS")
        self.assertIn("TECHNOLOGY_QUERY", plan.intents)
        self.assertEqual(len(plan.entities), 1)
        self.assertEqual(plan.entities[0].entity_id, "pld")
        self.assertEqual(len(plan.propositions), 1)
        self.assertEqual(plan.propositions[0].status, "UNVERIFIED")

    def test_b_multi_proposition_query(self):
        """Test B: Multi-proposition query -> 1 entity, 2 distinct propositions."""
        q = "Is PLD Space developing a reusable launch vehicle and how much funding have they raised?"
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "SUCCESS")
        self.assertIn("TECHNOLOGY_QUERY", plan.intents)
        self.assertIn("FUNDING_QUERY", plan.intents)
        self.assertEqual(len(plan.propositions), 2)
        
        preds = [p.predicate for p in plan.propositions]
        self.assertIn("develops", preds)
        self.assertIn("funded_by", preds)
        for p in plan.propositions:
            self.assertEqual(p.status, "UNVERIFIED")

    def test_c_comparison_query(self):
        """Test C: Comparison query -> 3 entities x 2 dimensions = 6 independent propositions."""
        q = "Compare PLD Space, Isar Aerospace and Rocket Factory Augsburg on reusable launch vehicle development and current status."
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "SUCCESS")
        self.assertIn("COMPARISON_QUERY", plan.intents)
        self.assertEqual(len(plan.entities), 3)
        
        ent_ids = [e.entity_id for e in plan.entities]
        self.assertIn("pld", ent_ids)
        self.assertIn("isar", ent_ids)
        self.assertIn("rfa", ent_ids)

        self.assertGreaterEqual(len(plan.propositions), 6)
        for p in plan.propositions:
            self.assertEqual(p.status, "UNVERIFIED")

    def test_d_entity_discovery_query(self):
        """Test D: Entity-discovery query -> ENTITY_DISCOVERY intent & ENTITY_CLASS type."""
        q = "Which European launch companies are developing reusable launch vehicles?"
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "SUCCESS")
        self.assertIn("ENTITY_DISCOVERY", plan.intents)
        self.assertEqual(plan.constraints.get("geography"), "European")
        self.assertTrue(any(e.entity_type == "ENTITY_CLASS" for e in plan.entities))
        self.assertEqual(plan.propositions[0].status, "UNVERIFIED")

    def test_e_technology_query(self):
        """Test E: Technology query -> TECHNOLOGY_QUERY intent & RFA entity."""
        q = "What reusable technology is Rocket Factory Augsburg designing?"
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "SUCCESS")
        self.assertIn("TECHNOLOGY_QUERY", plan.intents)
        self.assertEqual(plan.entities[0].entity_id, "rfa")

    def test_f_funding_query(self):
        """Test F: Funding query -> FUNDING_QUERY intent & funded_by predicate."""
        q = "How much funding has PLD Space received?"
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "SUCCESS")
        self.assertIn("FUNDING_QUERY", plan.intents)
        self.assertEqual(plan.propositions[0].predicate, "funded_by")

    def test_g_temporal_constraint_extraction(self):
        """Test G: Temporal constraint extraction -> HISTORICAL scope."""
        q = "PLD Space investigated reusable launch vehicle concepts in 2018."
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "SUCCESS")
        self.assertEqual(plan.temporal_scope, "HISTORICAL")

    def test_h_geographic_constraint_extraction(self):
        """Test H: Geographic constraint extraction -> German geography."""
        q = "German launch providers developing reusable rockets."
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "SUCCESS")
        self.assertEqual(plan.constraints.get("geography"), "German")

    def test_i_unknown_entity(self):
        """Test I: Unknown entity -> UNKNOWN_ENTITY type, not canonical Orvyra entity."""
        q = "Is Acme Launch developing a reusable rocket?"
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "SUCCESS")
        self.assertEqual(len(plan.entities), 1)
        self.assertEqual(plan.entities[0].entity_type, "UNKNOWN_ENTITY")

    def test_j_ambiguous_entity(self):
        """Test J: Ambiguous entity -> AMBIGUOUS_ENTITY status."""
        q = "Is ambiguous rocket company developing a reusable launcher?"
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "AMBIGUOUS_ENTITY")
        self.assertEqual(plan.error_code, "AMBIGUOUS_ENTITY")

    def test_k_unsupported_predicate(self):
        """Test K: Unsupported predicate -> UNSUPPORTED_PREDICATE status."""
        q = "Is PLD Space mind_controls reusable rockets?"
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.status, "UNSUPPORTED_PREDICATE")
        self.assertEqual(plan.error_code, "UNSUPPORTED_PREDICATE")

    def test_l_planner_does_not_assign_supported_status(self):
        """Test L: Planner NEVER assigns SUPPORTED or TRUE status to any proposition."""
        queries = [
            "Is PLD Space developing a reusable launch vehicle?",
            "Compare Isar Aerospace and Orbex on reusable rockets.",
            "How much funding has Rocket Factory Augsburg raised?"
        ]
        for q in queries:
            plan = build_deterministic_query_plan(q)
            for p in plan.propositions:
                self.assertEqual(p.status, "UNVERIFIED")
                self.assertNotEqual(p.status, "SUPPORTED")

    def test_m_planner_does_not_create_orvyra_relationships(self):
        """Test M: Planner execution leaves Orvyra graph state completely untouched."""
        q = "Compare PLD Space and Isar Aerospace on reusable launchers."
        plan = build_deterministic_query_plan(q)

        slice_res = OrvyraAdapter.build_vertical_slice(
            query=q,
            query_plan=plan.model_dump(),
            retrieved_passages=[],
            doc_map={},
            retrieval_stats={}
        )
        self.assertEqual(len(slice_res.claims), 0)
        self.assertEqual(len(slice_res.edges), 0)
        self.assertEqual(len(plan.propositions), 2)

    def test_n_compound_query_produces_independent_propositions(self):
        """Test N: Compound query produces independent propositions with unique IDs."""
        q = "Is PLD Space developing a reusable launcher and what is their current status?"
        plan = build_deterministic_query_plan(q)

        prop_ids = [p.proposition_id for p in plan.propositions]
        self.assertEqual(len(prop_ids), len(set(prop_ids)))  # All IDs unique
        self.assertGreaterEqual(len(plan.propositions), 2)

    def test_o_same_entity_multiple_propositions_remain_independent(self):
        """Test O: Multiple propositions for single entity remain distinct objects."""
        q = "Is PLD Space developing reusable rockets and how much funding do they have?"
        plan = build_deterministic_query_plan(q)

        pld_props = [p for p in plan.propositions if p.entity_id == "pld"]
        self.assertEqual(len(pld_props), 2)
        self.assertNotEqual(pld_props[0].predicate, pld_props[1].predicate)

    def test_p_existing_canonical_orvyra_entity_resolution(self):
        """Test P: Resolves all 5 canonical Orvyra entities correctly."""
        entities_test = [
            ("PLD Space", "pld"),
            ("Isar Aerospace", "isar"),
            ("Rocket Factory Augsburg", "rfa"),
            ("Orbex", "orbex"),
            ("MaiaSpace", "maia")
        ]
        for name, expected_id in entities_test:
            q = f"Is {name} developing reusable technology?"
            plan = build_deterministic_query_plan(q)
            self.assertEqual(plan.entities[0].entity_id, expected_id)

    def test_q_unknown_entity_does_not_create_new_entity(self):
        """Test Q: Unknown entity is flagged as UNKNOWN_ENTITY and creates no Orvyra entity."""
        q = "Is Starlight Space developing a reusable launch vehicle?"
        plan = build_deterministic_query_plan(q)

        self.assertEqual(plan.entities[0].entity_type, "UNKNOWN_ENTITY")
        self.assertNotIn(plan.entities[0].entity_id, ["pld", "isar", "rfa", "orbex", "maia"])

    def test_r_query_plan_is_deterministic_for_identical_input(self):
        """Test R: Identical query + identical ontology produces 100% identical plan across 5 runs."""
        q = "Compare PLD Space, Isar Aerospace and Rocket Factory Augsburg on reusable launch vehicle development and current status."
        plans = [build_deterministic_query_plan(q).model_dump() for _ in range(5)]

        for i in range(1, 5):
            self.assertEqual(plans[0], plans[i])

if __name__ == "__main__":
    unittest.main()
