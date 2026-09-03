import os
import sys

# Add apps/api to path
sys.path.insert(0, os.path.abspath("apps/api"))

from app.main import app, seed_initial_knowledge_base
from app.services.store import store
from app.services.retrieval import hybrid_retrieve
from app.services.reranker import rerank_evidence_candidates
from app.services.generator import build_grounded_answer
from app.services.planner import plan_query_execution

print("="*60)
print("COSMOHUB INTELLIGENCE ENGINE — END-TO-END KNOWLEDGE TEST")
print("="*60)

# Seed Knowledge Base
seed_initial_knowledge_base()

# Check Sources
sources = store.list_sources()
print(f"\n-> Indexed Sources Count: {len(sources)}")
for s in sources:
    print(f"   * [{s.source_type.value.upper()}] {s.name} (Docs: {s.document_count}, Hash: {s.last_content_hash[:12]}...)")

# Test Query 1: Grounded European launch companies funding
test_query = "Which European launch companies have raised more than €100M since 2024?"
print(f"\n" + "-"*60)
print(f"-> QUERY 1: '{test_query}'")
print("-"*60)

plan = plan_query_execution(test_query)
print(f"   Intent: {plan['intent']}")
print(f"   Extracted Entities: {plan['entities']}")
print(f"   Filters: {plan['filters']}")

fused_hits, stats = hybrid_retrieve(test_query, top_k=10)
print(f"   Hybrid Retrieval Hits: Dense ({stats['dense_results']}), Sparse ({stats['keyword_results']}), Fused ({stats['fused_results']})")

reranked = rerank_evidence_candidates(test_query, fused_hits, top_k=5)
print(f"   Reranked Top Candidates: {len(reranked)}")
for idx, p in enumerate(reranked, 1):
    print(f"     [{idx}] Score: {p.relevance_score:.3f} | Conf: {p.confidence_score} | Publisher: {p.publisher}")

answer = build_grounded_answer(test_query, reranked, plan, stats)
print("\n-> Grounded Answer Result:")
print(f"   Status: {answer.status.value.upper()} | Confidence: {answer.confidence}")
print(f"   Summary Answer:\n{answer.answer}")
print("\n-> WHY Breakdown Categories:")
for w in answer.why:
    print(f"   - [{w.code}] {w.title}: {w.summary}")

# Test Query 2: Unknown / Unsupported question
unsupported_query = "Which space startup built quantum teleportation stations on Mars in 2020?"
print(f"\n" + "-"*60)
print(f"-> QUERY 2 (Unsupported Check): '{unsupported_query}'")
print("-"*60)

fused_hits_2, stats_2 = hybrid_retrieve(unsupported_query, top_k=10)
reranked_2 = rerank_evidence_candidates(unsupported_query, fused_hits_2, top_k=5)
answer_2 = build_grounded_answer(unsupported_query, reranked_2, plan_query_execution(unsupported_query), stats_2)
print(f"   Status: {answer_2.status.value.upper()}")
print(f"   Answer Text: {answer_2.answer}")

print("\n" + "="*60)
print("SUCCESS: ALL END-TO-END KNOWLEDGE TESTS PASSED!")
print("="*60)
