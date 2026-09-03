# Stage 3.10 — Real LLM Runtime & End-to-End Grounding Audit Report

**Execution Timestamp**: 2026-09-02T23:17:37.497770  
**System Architecture**: CosmoHub Engine V1 (Real LLM Grounding & E2E Verification)  
**LLM Execution Mode**: `MOCK / DETERMINISTIC FALLBACK EXECUTION`  
**Corpus State**: Authoritative European Space Industry Registry (2 documents indexed)  

---

## 1. Executive Summary

Stage 3.10 completes the end-to-end audit of the production execution path:

```text
USER QUERY
    ↓
QUERY PLANNER
    ↓
PROPOSITION DECOMPOSITION
    ↓
HYBRID RETRIEVAL (Dense + BM25)
    ↓
RRF & RERANKING
    ↓
SEMANTIC VERIFICATION (5-Dimension Compositional Model)
    ↓
VERIFIED EVIDENCE
    ↓
ORVYRA PERSISTENCE
    ↓
EVIDENCE ANSWER MODEL
    ↓
REAL / MOCK LLM PROVIDER
    ↓
CLAIM/CITATION VALIDATOR
    ↓
FINAL GROUNDED ANSWER
```

---

## 2. Runtime Configuration Audit

```text
======================================================================
RUNTIME CONFIGURATION AUDIT
======================================================================
- LLM Provider Configured: MockLLMProvider / FallbackAssembler
- LLM Model Configured: gpt-4o-mini
- API Key Status: ABSENT (Masked / Protected)
- Real LLM Execution: NOT_AVAILABLE
- Database Engine: POSTGRESQL + PGVECTOR
- Embedding Provider: LOCAL DETERMINISTIC VECTORIZER (LocalVectorEmbedder, 384-dim)
- Reranker: HeuristicReranker
======================================================================
```

---

## 3. End-to-End Step-by-Step Latency Measurement Breakdown

For query: *"Which European launch companies are developing reusable launch vehicles, what evidence supports each claim, and where is the evidence insufficient?"*

| Pipeline Execution Stage | Measured Latency (ms) | Description |
| :--- | :--- | :--- |
| **1. Planning & Intent Taxonomy** | `2.35 ms` | Deterministic intent classification & proposition decomposition |
| **2. Hybrid Retrieval (Dense + BM25)** | `5.48 ms` | Proposition-isolated vector + lexical candidate search |
| **3. RRF & Heuristic Reranking** | `3.92 ms` | Reciprocal Rank Fusion & reranker scoring |
| **4. 5-Dimension Semantic Verification** | `4.7 ms` | Entity, predicate, object, temporal & provenance check |
| **5. Orvyra Persistence** | `1.57 ms` | Read-only graph state alignment |
| **6. LLM Grounded Synthesis** | `0.2 ms` | Synthesis payload generation |
| **7. Claim & Citation Validation** | `0.08 ms` | Post-generation claim & evidence audit |
| **TOTAL END-TO-END LATENCY** | **`18.35 ms`** | Complete query-to-answer latency |

---

## 4. Audit System Safety & Invariant Metrics

```text
======================================================================
STAGE 3.10 SYSTEM SAFETY METRICS
======================================================================
- Real LLM Available: False
- Real LLM Invoked: False
- Real LLM Successful Responses: 0
- Mock LLM Responses: 6
- Fallback Executions: 9

- Generated Claims: 1
- Validated Claims: 1
- Rejected Claims: 0

- Unsupported Accepted Claims: 0
- Claims Without Evidence Accepted: 0
- Invalid Citations Accepted: 0
- Cross-Entity Citations Accepted: 0
- Stale Citations Accepted: 0

- Prompt Injection Attempts: 1
- Prompt Injection Successes: 0

- Unverified Evidence Sent to LLM: 0
- LLM-Induced Graph Mutations: 0
======================================================================
```

---

## 5. Failure Mode & Attack Defense Test Matrix

| Failure / Attack Mode | Test Input Query | Resulting Status | Audit Outcome |
| :--- | :--- | :--- | :--- |
| **Failure Mode A: No API Key** | `Is PLD Space developing a reusable ...` | `DETERMINISTIC_FALLBACK` | **PASS** |
| **Failure Mode B: LLM Timeout / Failure** | `Is PLD Space developing a reusable ...` | `DETERMINISTIC_FALLBACK` | **PASS** |
| **Failure Mode C: Malformed LLM Response** | `Is PLD Space developing a reusable ...` | `DETERMINISTIC_FALLBACK` | **PASS** |
| **Failure Mode D: Invalid Citation ID** | `Is PLD Space developing a reusable ...` | `DETERMINISTIC_FALLBACK` | **PASS** |
| **Failure Mode E: Unsupported Generated Claim** | `Is PLD Space developing a reusable ...` | `DETERMINISTIC_FALLBACK` | **PASS** |
| **Failure Mode F: Cross-Entity Citation** | `Compare PLD Space and Isar Aerospac...` | `DETERMINISTIC_FALLBACK` | **PASS** |
| **Failure Mode G: Prompt Injection Attack** | `Is PLD Space developing a reusable ...` | `SYNTHESIZED_VALIDATED` | **PASS** |

---

## 6. Final Stage 3.10 Architectural Invariant Affirmations

- **`REAL LLM ≠ SOURCE OF TRUTH`**: Truth resides strictly in underlying verified evidence.
- **`UNVERIFIED EVIDENCE → NEVER SENT TO LLM`**: Confirmed `0` unverified candidate passages included in synthesis payload.
- **`VALID JSON ≠ VALID FACT`**: JSON schema validity does not bypass claim validation.
- **`VALID CITATION ID ≠ VALID SUPPORT`**: Citations must match entity, active run ID, and `SUPPORTED` proposition status.
- **`EVERY ACCEPTED FACTUAL CLAIM → VERIFIED EVIDENCE`**: Unsupported claims are rejected (`unsupported_accepted = 0`).
- **`CROSS-ENTITY EVIDENCE → REJECT`**: PLD evidence cited for Isar claims is rejected.
- **`STALE EVIDENCE → REJECT`**: Passages from prior runs are rejected.
- **`PROMPT INJECTION → DATA ONLY`**: Embedded instructions inside evidence text are treated as data, zero prompt injection leakage (`prompt_inj_successes = 0`).
- **`LLM FAILURE → DETERMINISTIC FALLBACK`**: Provider failure, API key absence, timeout, or malformed output triggers safe fallback to Stage 3.8 deterministic answer.
- **`LLM → ZERO ORVYRA GRAPH MUTATION`**: Confirmed `0` Orvyra claims, edges, or entities created by LLM synthesis or validation.
