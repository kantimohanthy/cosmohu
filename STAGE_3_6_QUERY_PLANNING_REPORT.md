# STAGE 3.6 QUERY PLANNING & PROPOSITION DECOMPOSITION REPORT

---

## 1. PLANNER ARCHITECTURE

The Query Planner acts as a **deterministic, ontology-aware research coordinator**. It decomposes natural language user queries into structured proposition sets without performing factual truth evaluation:

```text
USER QUERY -> QUERY PLAN -> PROPOSITION SET -> EVIDENCE RETRIEVAL -> SEMANTIC VERIFICATION -> VERIFIED CLAIMS -> ORVYRA
```

**Core Separation of Concerns:**
- **QUERY PLANNER:** Determines *what needs to be investigated* (Initial proposition status: `UNVERIFIED`).
- **EVIDENCE RETRIEVER:** Identifies candidate passages from authoritative source roots.
- **SEMANTIC VERIFIER:** Evaluates 5-dimension entailment (`ENTAILED`, `NOT_ENTAILED`, `CONTRADICTED`).
- **ORVYRA GRAPH ADAPTER:** Persists verified claims and corroborating evidence edges.
- **LLM LAYER:** Future synthesis/explanation layer (inactive during Stage 3.6).


---

## 2. QUERY-PLAN SCHEMA

Every plan conforms to the explicit Pydantic schema (`QueryPlan`):
```python
class QueryPlan(BaseModel):
    query_id: str
    original_query: str
    intents: List[str]
    entities: List[ResolvedEntity]
    propositions: List[QueryProposition]
    constraints: Dict[str, Any]
    temporal_scope: str = 'UNKNOWN'
    requested_evidence: bool = False
    comparison_dimensions: List[str]
    status: str = 'SUCCESS'  # SUCCESS | AMBIGUOUS_ENTITY | UNSUPPORTED_PREDICATE | UNSUPPORTED_DIMENSION
```


---

## 3. SUPPORTED INTENT TAXONOMY

The planner uses a controlled intent taxonomy rather than free-form labels:
- `ATTRIBUTE_QUERY`
- `COMPARISON_QUERY`
- `ENTITY_DISCOVERY`
- `EVIDENCE_QUERY`
- `FUNDING_QUERY`
- `RELATIONSHIP_QUERY`
- `STATUS_QUERY`
- `TECHNOLOGY_QUERY`

---

## 4. CONTROLLED PROPOSITION VOCABULARY

### Predicates:
- `develops` (Aliases: developing, develop, develops)
- `operates` (Aliases: operating, operates, operate)
- `manufactures` (Aliases: manufacturing, manufactures, manufacture)
- `funded_by` (Aliases: funding, funded, raised)
- `headquartered_in` (Aliases: headquartered, based in, located in)
- `launches` (Aliases: launching, launches, launched)
- `uses` (Aliases: using, uses, utilizes)
- `partners_with` (Aliases: partnering, partners, partnered)
- `acquired_by` (Aliases: acquisition, acquired)

### Technology Concepts:
- `reusable_launch_vehicle` (Phrases: reusable launch vehicle, reusable launcher)
- `reusable_first_stage` (Phrases: reusable first stage, recoverable first stage)
- `launch_vehicle` (Phrases: launch vehicle, launcher)
- `rocket` (Phrases: rocket)
- `satellite` (Phrases: satellite, payload)
- `launch_site` (Phrases: launch site, spaceport)

---

## 5. SINGLE-QUERY DECOMPOSITION EXAMPLES

### Query: *"Is PLD Space developing a reusable launch vehicle?"*
```json
{
  "query_id": "plan_eb2a6f14204e",
  "original_query": "Is PLD Space developing a reusable launch vehicle?",
  "intents": [
    "TECHNOLOGY_QUERY"
  ],
  "entities": [
    {
      "entity_id": "pld",
      "canonical_name": "PLD Space",
      "entity_type": "CANONICAL_ENTITY",
      "category_constraint": null,
      "geographic_constraint": "Spanish"
    }
  ],
  "propositions": [
    {
      "proposition_id": "PROP-PLD-REUSABLE-001",
      "entity_id": "pld",
      "entity_name": "PLD Space",
      "predicate": "develops",
      "target_object": "reusable_launch_vehicle",
      "temporal_scope": "IN_DEVELOPMENT",
      "required_evidence": [
        "entity attribution",
        "predicate support",
        "object support",
        "temporal support",
        "valid provenance"
      ],
      "status": "UNVERIFIED"
    }
  ],
  "constraints": {},
  "temporal_scope": "IN_DEVELOPMENT",
  "requested_evidence": false,
  "comparison_dimensions": [],
  "status": "SUCCESS",
  "error_code": null,
  "reason": ""
}
```


---

## 6. COMPOUND & COMPARISON QUERY DECOMPOSITION EXAMPLES

### Query: *"Compare PLD Space, Isar Aerospace and Rocket Factory Augsburg on reusable launch vehicle development and current status."*
```json
{
  "query_id": "plan_682f14c4b6ad",
  "original_query": "Compare PLD Space, Isar Aerospace and Rocket Factory Augsburg on reusable launch vehicle development and current status.",
  "intents": [
    "COMPARISON_QUERY",
    "TECHNOLOGY_QUERY",
    "STATUS_QUERY"
  ],
  "entities": [
    {
      "entity_id": "pld",
      "canonical_name": "PLD Space",
      "entity_type": "CANONICAL_ENTITY",
      "category_constraint": null,
      "geographic_constraint": "Spanish"
    },
    {
      "entity_id": "isar",
      "canonical_name": "Isar Aerospace",
      "entity_type": "CANONICAL_ENTITY",
      "category_constraint": null,
      "geographic_constraint": "German"
    },
    {
      "entity_id": "rfa",
      "canonical_name": "Rocket Factory Augsburg",
      "entity_type": "CANONICAL_ENTITY",
      "category_constraint": null,
      "geographic_constraint": "German"
    }
  ],
  "propositions": [
    {
      "proposition_id": "PROP-PLD-REUSABLE-001",
      "entity_id": "pld",
      "entity_name": "PLD Space",
      "predicate": "develops",
      "target_object": "reusable_launch_vehicle",
      "temporal_scope": "IN_DEVELOPMENT",
      "required_evidence": [
        "entity attribution",
        "predicate support",
        "object support",
        "temporal support",
        "valid provenance"
      ],
      "status": "UNVERIFIED"
    },
    {
      "proposition_id": "PROP-PLD-STATUS-002",
      "entity_id": "pld",
      "entity_name": "PLD Space",
      "predicate": "has_development_status",
      "target_object": "development_status",
      "temporal_scope": "CURRENT",
      "required_evidence": [
        "entity attribution",
        "predicate support",
        "object support",
        "temporal support",
        "valid provenance"
      ],
      "status": "UNVERIFIED"
    },
    {
      "proposition_id": "PROP-ISAR-REUSABLE-003",
      "entity_id": "isar",
      "entity_name": "Isar Aerospace",
      "predicate": "develops",
      "target_object": "reusable_launch_vehicle",
      "temporal_scope": "IN_DEVELOPMENT",
      "required_evidence": [
        "entity attribution",
        "predicate support",
        "object support",
        "temporal support",
        "valid provenance"
      ],
      "status": "UNVERIFIED"
    },
    {
      "proposition_id": "PROP-ISAR-STATUS-004",
      "entity_id": "isar",
      "entity_name": "Isar Aerospace",
      "predicate": "has_development_status",
      "target_object": "development_status",
      "temporal_scope": "CURRENT",
      "required_evidence": [
        "entity attribution",
        "predicate support",
        "object support",
        "temporal support",
        "valid provenance"
      ],
      "status": "UNVERIFIED"
    },
    {
      "proposition_id": "PROP-RFA-REUSABLE-005",
      "entity_id": "rfa",
      "entity_name": "Rocket Factory Augsburg",
      "predicate": "develops",
      "target_object": "reusable_launch_vehicle",
      "temporal_scope": "IN_DEVELOPMENT",
      "required_evidence": [
        "entity attribution",
        "predicate support",
        "object support",
        "temporal support",
        "valid provenance"
      ],
      "status": "UNVERIFIED"
    },
    {
      "proposition_id": "PROP-RFA-STATUS-006",
      "entity_id": "rfa",
      "entity_name": "Rocket Factory Augsburg",
      "predicate": "has_development_status",
      "target_object": "development_status",
      "temporal_scope": "CURRENT",
      "required_evidence": [
        "entity attribution",
        "predicate support",
        "object support",
        "temporal support",
        "valid provenance"
      ],
      "status": "UNVERIFIED"
    }
  ],
  "constraints": {},
  "temporal_scope": "UNKNOWN",
  "requested_evidence": false,
  "comparison_dimensions": [
    "reusable_launch_vehicle",
    "status"
  ],
  "status": "SUCCESS",
  "error_code": null,
  "reason": ""
}
```


---

## 7. AMBIGUITY AND UNSUPPORTED-QUERY HANDLING

### Query: *"Is ambiguous rocket company developing a reusable launcher?"*
- **Status:** `AMBIGUOUS_ENTITY`
- **Reason:** AMBIGUOUS_ENTITY: Term 'ambiguous rocket company' matches multiple entities without disambiguation.

### Query: *"Is PLD Space mind_controls reusable rockets?"*
- **Status:** `UNSUPPORTED_PREDICATE`
- **Reason:** UNSUPPORTED_PREDICATE: Predicate 'mind_controls' is outside controlled ontology vocabulary.

### Query: *"Compare PLD Space and Isar Aerospace on astrological sign and flavor."*
- **Status:** `UNSUPPORTED_DIMENSION`
- **Reason:** UNSUPPORTED_DIMENSION: Comparison dimension 'flavor' is not supported by space ontology.


---

## 8. DETERMINISM & REPEATABILITY RESULTS

- **Deterministic Repeatability:** `PASS (True)`
- **Runs Evaluated per Query:** 3 identical executions per query
- **Variance:** `0.0%` (100% byte-for-byte identical output)


---

## 9. AUTOMATED TEST SUITE SUMMARY

Executed `tests/test_stage3_6_query_planner.py` (**18/18 PASSED** in 0.017s):
- **Test A (Single proposition):** `PASS`
- **Test B (Multi-proposition):** `PASS`
- **Test C (Comparison query):** `PASS` ($3 \text{ entities} \times 2 \text{ dimensions} = 6 \text{ propositions}$)
- **Test D (Entity discovery):** `PASS` (`ENTITY_CLASS` resolution)
- **Test E (Technology query):** `PASS` (`rfa` resolution)
- **Test F (Funding query):** `PASS` (`funded_by` predicate)
- **Test G (Temporal extraction):** `PASS` (`HISTORICAL` scope)
- **Test H (Geographic extraction):** `PASS` (`German` constraint)
- **Test I (Unknown entity):** `PASS` (`UNKNOWN_ENTITY` type)
- **Test J (Ambiguous entity):** `PASS` (`AMBIGUOUS_ENTITY` error)
- **Test K (Unsupported predicate):** `PASS` (`UNSUPPORTED_PREDICATE` error)
- **Test L (No SUPPORTED status assigned):** `PASS` (All propositions `UNVERIFIED`)
- **Test M (No Orvyra relationships created):** `PASS` (0 claims, 0 edges created)
- **Test N (Compound independent propositions):** `PASS` (Unique IDs)
- **Test O (Multiple propositions per entity):** `PASS` (Independent objects)
- **Test P (Canonical entity resolution):** `PASS` (All 5 Orvyra entities resolved)
- **Test Q (Unknown entity isolation):** `PASS` (No entity creation)
- **Test R (Deterministic repeatability):** `PASS` (100% identical output across 5 runs)

---

## 10. EXPLICIT INVARIANT CONFIRMATION

- **Planner created claims:** `0` (CONFIRMED ZERO)
- **Planner created graph relationships:** `0` (CONFIRMED ZERO)
- **Planner assigned truth/SUPPORTED status:** `False` (CONFIRMED ALL `UNVERIFIED`)
- **Planner bypassed semantic verifier:** `False` (CONFIRMED VERIFIER STILL REQUIRED)

---

## 11. SUMMARY METRICS TABLE

| Metric | Result |
| :--- | :--- |
| **Total Queries Tested** | `13` |
| **Total Propositions Generated** | `16` |
| **Intents Detected** | `ATTRIBUTE_QUERY, COMPARISON_QUERY, ENTITY_DISCOVERY, FUNDING_QUERY, RELATIONSHIP_QUERY, STATUS_QUERY, TECHNOLOGY_QUERY` |
| **Canonical Entity Resolutions** | `9` |
| **Unknown Entity Resolutions** | `1` |
| **Ambiguous / Unsupported Cases** | `3` |
| **Deterministic Repeatability** | `100.0% PASS` |
| **Automated Test Pass Rate** | `18/18 (100%)` |