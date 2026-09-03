import time
from typing import List, Dict, Any
from app.services.retrieval import hybrid_retrieve
from app.services.reranker import rerank_evidence_candidates
from app.services.store import store

EVALUATION_DATASET = [
    {
        "id": "eval_1",
        "question": "Which European launch companies have raised more than €100M?",
        "expected_entities": ["Isar Aerospace", "PLD Space", "MaiaSpace", "Orbex"],
        "expected_keywords": ["funding", "isar", "pld space", "maiaspace", "orbex", "310"],
    },
    {
        "id": "eval_2",
        "question": "What is the budget and primary objective of the IRIS² satellite constellation?",
        "expected_entities": ["IRIS²", "EUSPA", "European Union"],
        "expected_keywords": ["iris²", "6.0", "broadband", "secure", "constellation"],
    },
    {
        "id": "eval_3",
        "question": "What are the specs and launch dates for Ariane 6?",
        "expected_entities": ["Ariane 6", "ArianeGroup"],
        "expected_keywords": ["ariane 6", "2024", "heavy", "vinci", "21600"],
    },
    {
        "id": "eval_4",
        "question": "Which company is developing the EAGLE-1 Quantum Key Distribution satellite?",
        "expected_entities": ["SES", "ESA", "EAGLE-1"],
        "expected_keywords": ["eagle-1", "ses", "quantum", "qkd", "180"],
    }
]

def run_evaluation_suite() -> Dict[str, Any]:
    """Runs end-to-end retrieval benchmarking across the evaluation dataset."""
    results = []

    for item in EVALUATION_DATASET:
        q_id = item["id"]
        q_text = item["question"]
        expected_kws = item["expected_keywords"]

        # 1. Baseline Dense
        t0 = time.time()
        dense_hits = store.search_vector_dense(store._get_connection().cursor() if hasattr(store, 'embedder') else [0.0]*384, top_k=10)
        t_dense = (time.time() - t0) * 1000

        # 2. Hybrid Retrieval
        t1 = time.time()
        fused_hits, stats = hybrid_retrieve(q_text, top_k=10)
        t_hybrid = (time.time() - t1) * 1000

        # 3. Hybrid + Reranking
        t2 = time.time()
        reranked_passages = rerank_evidence_candidates(q_text, fused_hits, top_k=5)
        t_rerank = (time.time() - t2) * 1000

        # Evaluate keyword match precision
        matched_kws = 0
        all_text = " ".join([p.text.lower() for p in reranked_passages])
        for kw in expected_kws:
            if kw in all_text:
                matched_kws += 1

        recall = matched_kws / max(1, len(expected_kws))

        results.append({
            "eval_id": q_id,
            "question": q_text,
            "dense_hit_count": len(dense_hits),
            "hybrid_hit_count": len(fused_hits),
            "reranked_passage_count": len(reranked_passages),
            "recall_score": round(recall, 2),
            "latency_ms": {
                "dense": round(t_dense, 1),
                "hybrid": round(t_hybrid, 1),
                "rerank": round(t_rerank, 1)
            }
        })

    avg_recall = sum(r["recall_score"] for r in results) / max(1, len(results))

    return {
        "dataset_size": len(EVALUATION_DATASET),
        "average_recall": round(avg_recall, 2),
        "results": results
    }
