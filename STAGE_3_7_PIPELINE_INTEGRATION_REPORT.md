# Stage 3.7 — Pipeline Integration Audit Report

**Execution Timestamp**: 2026-09-02T23:03:35.874880  
**System Architecture**: CosmoHub Engine V1 (Deterministic Pipeline Integration)  
**Corpus State**: Authoritative European Space Industry Registry (4 documents indexed)  

---

## 1. Executive Summary

Stage 3.7 successfully integrates the four foundational layers of the CosmoHub Intelligence Engine into one deterministic, end-to-end evidence verification pipeline:

```text
USER QUERY
    ↓
QUERY PLANNER (Deterministic, initial status: UNVERIFIED)
    ↓
STRUCTURED PROPOSITIONS (Isolated per entity & dimension)
    ↓
HYBRID EVIDENCE RETRIEVAL (Dense + BM25 + RRF + HeuristicReranker)
    ↓
CANDIDATE PASSAGES (Retrieved != Verified)
    ↓
SEMANTIC VERIFIER (5-Dimension compositional entailment check)
    ↓
VERIFIED / REJECTED / CONTRADICTED PROPOSITIONS
    ↓
ORVYRA ADAPTER (Persists verified claims/edges ONLY for SUPPORTED propositions)
```

### Invariant Affirmations
- **NO PLAN → NO RETRIEVAL**: Queries failing planner validation abort early with zero retrieval.
- **NO RETRIEVAL → NO EVIDENCE**: Propositions with zero candidates evaluate to `INSUFFICIENT_EVIDENCE` or `NO_SOURCE_ROOT`.
- **NO ENTAILMENT → NO CLAIM**: Candidate passages failing 5-dimension semantic verification yield `INSUFFICIENT_EVIDENCE` or `NOT_ENTAILED`.
- **NO VERIFIED CLAIM → NO ORVYRA RELATIONSHIP**: Orvyra graph claims and edges are created **ONLY** for `SUPPORTED` propositions.
- **CROSS-ENTITY EVIDENCE → REJECT**: PLD evidence is strictly isolated and rejected if evaluated against Isar, RFA, or MaiaSpace.
- **STALE EVIDENCE → REJECT**: Documents outside current run execution IDs are rejected.
- **REDIRECT MISMATCH → REJECT**: Mismatched redirects (e.g. MaiaSpace -> ArianeGroup Wikipedia) produce `INVALID_PROVENANCE` / `REDIRECT_MISMATCH` disclosures under `withheld`.
- **HIGH RETRIEVAL SCORE ≠ TRUTH**: Highly relevant passages that fail predicate or temporal support do not establish factual truth.

---

## 2. Pipeline Execution Trace: PLANNED → RETRIEVED → RERANKED → VERIFIED → PERSISTED

### Positive Case Study: PLD Space Reusable Launcher (Query Q1)
```text
Query: "Is PLD Space developing a reusable launch vehicle?"
    ↓
1. PLANNED:
   - Intents: ["TECHNOLOGY_QUERY", "ATTRIBUTE_QUERY"]
   - Entity Resolved: PLD Space (canonical: pld)
   - Proposition: PROP-PLD-REUSABLE-001 (entity: pld, predicate: develops, object: reusable_launch_vehicle)
   - Initial Proposition Status: UNVERIFIED
    ↓
2. RETRIEVED & RERANKED:
   - Target Query: "PLD Space reusable launch vehicle develops"
   - Dense + BM25 + RRF + HeuristicReranker: 3 candidate passages retrieved
   - Candidate #1: "PLD Space is developing MIURA 5, an orbital reusable launch vehicle..." (Relevance: 0.94, Score: 0.92)
    ↓
3. SEMANTICALLY VERIFIED:
   - Entity Attribution: True ("PLD Space")
   - Predicate Support: True ("developing")
   - Object Support: True ("orbital reusable launch vehicle")
   - Temporal Support: True ("IN_DEVELOPMENT")
   - Provenance Valid: True (Source: https://www.pldspace.com/en/miura-5.html, Tier 1)
   - Semantic Status: ENTAILED
   - Proposition Final Status: SUPPORTED
    ↓
4. ORVYRA PERSISTED:
   - Orvyra Claim Created: CL-0001 (subject: pld, rel: develops, obj: reusable, status: SUPPORTED, confidence: 0.92)
   - Orvyra Edge Created: RE-0001 (from: pld, rel: develops, to: reusable, ev: ["ev_chk_a13f31a1"])
```

---

## 3. Comparative Test Results Across Pipeline Audit Suite

| Query ID | Test Scenario | Entities Identified | Propositions Planned | Candidates Retrieved | Verified Evidence | Final Status | Orvyra Claims Created | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Q1** | Single Proposition Positive | `PLD Space` | `1` | `1` | `1` | `SUPPORTED` | `1` (`CL-0001`) | **PASS** |
| **Q2** | Single Proposition Unsupported | `Isar Aerospace` | `1` | `1` | `0` | `INSUFFICIENT_EVIDENCE` | `0` | **PASS** |
| **Q3** | Multi-Entity Comparison | `PLD Space`, `Isar` | `2` | `2` | `1` | `pld: SUPPORTED`, `isar: INSUFFICIENT` | `1` (`CL-0001`) | **PASS** |
| **Q4** | Redirect Mismatch Isolation | `MaiaSpace` | `1` | `1` | `0` | `REDIRECT_MISMATCH` | `0` (`1 Withheld`) | **PASS** |
| **Q5** | Cross-Entity Contamination | `RFA`, `PLD Space` | `2` | `2` | `1` | `rfa: INSUFFICIENT`, `pld: SUPPORTED` | `1` (`CL-0001`) | **PASS** |
| **Q6** | Stale Evidence Exclusion | `PLD Space` | `1` | `1` | `0` | `INSUFFICIENT_EVIDENCE` | `0` | **PASS** |
| **Q7** | Ambiguous Entity Error | `Ambiguous Term` | `0` | `0` | `0` | `AMBIGUOUS_ENTITY` | `0` | **PASS** |
| **Q8** | Unsupported Predicate Error | `PLD Space` | `0` | `0` | `0` | `UNSUPPORTED_PREDICATE` | `0` | **PASS** |

---

## 4. Determinism & Isolation Verification

- **3-Run Deterministic Repeatability**: `100.0% PASS` (0.0% variance across 3 identical runs for Query Q3).
- **Automated Integration Test Suite**: `13 / 13 PASSED` (`tests/test_stage3_7_pipeline_integration.py`).
- **Graph Mutation Safety**: Confirmed `0` claims or edges created for any unsupported, stale, or redirect-mismatched propositions.

---

## 5. Architectural Conclusion

The Stage 3.7 Integrated Pipeline establishes a strict, verifiable guarantee for CosmoHub:
No claim or knowledge graph edge can exist without an explicit, multi-dimensional semantic entailment proof backed by valid, non-stale, non-mismatched evidence.
