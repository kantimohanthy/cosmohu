import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath("apps/api"))

from app.main import seed_initial_knowledge_base
from app.services.crawler import fetch_web_page, determine_source_tier, SourceQualityTier
from app.services.parsers import WebParser
from app.services.chunker import chunk_document
from app.services.embedder import get_embedder
from app.services.store import store
from app.services.retrieval import hybrid_retrieve
from app.services.reranker import rerank_evidence_candidates, HeuristicReranker
from app.services.planner import plan_query_execution
from app.services.orvyra_adapter import OrvyraAdapter
from app.config import settings

print("================================================================================")
print("ORVYRA + COSMOHUB INTEGRATION TEST -- VERIFICATION & PROVENANCE CONTROL")
print("================================================================================")

# 1. Seed Initial Knowledge Base
seed_initial_knowledge_base()

# 2. Ingest Real Public Source with Redirect Identity Mismatch
target_url = "https://en.wikipedia.org/wiki/MaiaSpace"
print(f"\n--- 1. INGESTING REAL PUBLIC SOURCE DOCUMENT ({target_url}) ---")

crawled = fetch_web_page(target_url)

print(f"REQUESTED URL: {crawled['requested_url']}")
print(f"FINAL RESOLVED URL: {crawled['final_resolved_url']}")
print(f"WAS REDIRECTED: {crawled['was_redirected']}")
print(f"IDENTITY MISMATCH DETECTED: {crawled['identity_mismatch']}")
print(f"DOCUMENT TITLE: {crawled['title']}")
print(f"SOURCE QUALITY TIER: {crawled['source_tier']}")

doc = WebParser().parse(source_id="src_maiaspace_wiki", raw_data=crawled, url_or_path=target_url, publisher=crawled["publisher"])
store.save_document(doc)
chunks = chunk_document(doc)
embedder = get_embedder()
embeddings = embedder.embed_texts([c.content for c in chunks])
store.save_chunks(chunks, embeddings)

print(f"Ingested '{doc.title}' (ID: {doc.document_id}, Chunks: {len(chunks)}, Hash: {doc.content_hash[:12]}...)")

# ASSERT TASK 1 & TASK 7: Verification must fail if identity mismatch is not flagged!
assert crawled['identity_mismatch'] == True, "FAIL: Identity mismatch was NOT detected for redirected MaiaSpace URL!"
print("PASS: Redirect Identity Mismatch correctly detected.")

# 3. RUN INTEGRATION TEST QUERY
test_query = "Which European launch companies are developing reusable launch technology, what evidence supports each claim, and where is the evidence insufficient?"
print(f"\n" + "-"*80)
print(f"-> EXECUTING INTEGRATION TEST QUERY:")
print(f"   '{test_query}'")
print("-"*80)

t0 = time.time()
plan = plan_query_execution(test_query)
fused_hits, stats = hybrid_retrieve(test_query, top_k=20)
reranked = rerank_evidence_candidates(test_query, fused_hits, top_k=5)

doc_map = {}
for p in reranked:
    d = store.get_document(p.document_id)
    if d:
        doc_map[p.document_id] = {
            "content_hash": d.content_hash,
            "version": d.version,
            "publisher": d.publisher,
            "source_url": d.source_url,
            "extra": d.metadata.extra
        }

orvyra_response = OrvyraAdapter.build_vertical_slice(
    query=test_query,
    query_plan=plan,
    retrieved_passages=reranked,
    doc_map=doc_map,
    retrieval_stats=stats
)
latency_ms = (time.time() - t0) * 1000

# 4. ASSERTIONS & VERIFICATION OF EVIDENCE CONTRACT INVARIANTS
print(f"\n--- EXECUTION METRICS ---")
print(f"Response Status: {orvyra_response.status}")
print(f"Overall Confidence: {orvyra_response.confidence * 100:.0f}%")
print(f"Execution Latency: {latency_ms:.1f} ms")

print(f"\n--- PROVIDER TRANSPARENCY METADATA ---")
for k, v in orvyra_response.providers_metadata.items():
    print(f"  * {k}: {v}")

# ASSERT TASK 3: Reranker provider name transparency
assert orvyra_response.providers_metadata["reranker_provider"] == "HeuristicReranker", "FAIL: Reranker must be named HeuristicReranker!"
print("PASS: Reranker provider correctly reported as HeuristicReranker.")

# ASSERT TASK 1 & TASK 7: Redirected ArianeGroup page must NOT be treated as supported evidence for MaiaSpace!
maia_claims = [c for c in orvyra_response.claims if c.subject_id == "maia"]
assert len(maia_claims) == 0, "FAIL: Redirected ArianeGroup page was incorrectly treated as direct supported evidence for MaiaSpace!"
print("PASS: Redirected page was correctly REJECTED as direct evidence for MaiaSpace.")

# ASSERT TASK 7: Mismatch must be explicitly recorded in withheld disclosures
mismatch_withheld = [w for w in orvyra_response.withheld if "REDIRECT_MISMATCH" in w.reason]
assert len(mismatch_withheld) > 0, "FAIL: REDIRECT_MISMATCH reason was not recorded under withheld disclosures!"
print(f"PASS: REDIRECT_MISMATCH recorded in withheld disclosures ({mismatch_withheld[0].reason[:90]}...).")

print(f"\n--- ORVYRA CANONICAL ENTITIES ({len(orvyra_response.entities)}) ---")
for e in orvyra_response.entities:
    print(f"  * [{e.kind.upper()}] {e.name} (ID: {e.id}, Region: {e.region or 'Global'})")

print(f"\n--- EVIDENCE QUALITY TIERS & PROVENANCE ---")
for ev in orvyra_response.evidence:
    print(f"  * EV ID: {ev.id} | Tier: {ev.source_tier} | Strength: {ev.evidence_strength} | Conf: {ev.confidence} | Redirect Mismatch: {ev.identity_mismatch} | URL: {ev.sourceUri}")

print(f"\n--- UNSUPPORTED / WITHHELD DISCLOSURES ({len(orvyra_response.withheld)}) ---")
for w in orvyra_response.withheld:
    print(f"  * Entity: {w.entity_id} | Field: {w.field}")
    print(f"    Reason: {w.reason}")

print(f"\n" + "="*80)
print("FINAL GROUNDED SYNTHESIS:")
print("="*80)
print(orvyra_response.answer)

print("\n" + "="*80)
print("INTEGRATION VERIFICATION SUCCESSFUL -- ALL QUALITY & PROVENANCE INVARIANTS PASSED")
print("="*80)
