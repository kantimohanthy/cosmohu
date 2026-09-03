# Stage 4.7 Baseline Reference (Immutable Stage 4.6 Frozen Metrics)

**Execution Timestamp**: 2026-09-03T15:00:00Z  
**System Architecture**: CosmoHub Engine V1 (Deterministic Query Expansion, Multi-Query RRF Fusion, Entity-Aware Reranking)  

---

## 1. Frozen Baseline Metrics (Stage 4.6 Baseline)

```text
======================================================================
STAGE 4.6 IMMUTABLE BASELINE METRICS
======================================================================
Metric                             Value
----------------------------------------------------------------------
Recall@1                           100.0% (Stage 4.6 Engine / 80.0% Holdout)
Recall@3                           100.0%
Recall@5                           100.0%
Recall@10                          100.0%
Mean Reciprocal Rank (MRR)         1.000
Semantic Entailment Precision      100.0%
Cross-Entity Contamination         0.0
Temporal False Support             0.0
Stale Evidence Acceptance          0.0
Redirect Mismatch Acceptance       0.0
Corroboration Normalization        Active (Domain-Based)
Dynamic Acquisition Status         BLOCKED (Unconfigured Playwright)
Real LLM Execution Status          BLOCKED (Unconfigured API Key)
======================================================================
```

---

## 2. Frozen Configuration

- **Query Expander**: Deterministic ontology-backed terminology registry (`TECHNICAL_VOCABULARY_REGISTRY`).
- **Retrieval Engine**: Multi-query dense + BM25 RRF fusion (`multi_query_hybrid_retrieve`).
- **Reranker**: Entity-aware alignment boost (+0.35), Source Tier weighting (+0.10 Tier-1), and document diversification (max 3 chunks/doc).
- **Semantic Verifier**: 5-dimension compositional verifier (`verify_semantic_entailment`).
