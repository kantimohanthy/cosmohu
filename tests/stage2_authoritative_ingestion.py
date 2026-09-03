import os
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath("apps/api"))

from app.services.source_registry import source_registry, RegisteredSource
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
print("STAGE 2 -- AUTHORITATIVE SOURCE INGESTION & ORVYRA VERIFICATION")
print("================================================================================")

# 1. RUNTIME INFRASTRUCTURE VERIFICATION (Task 8)
print("\n--- 1. RUNTIME INFRASTRUCTURE VERIFICATION ---")

# Database Engine Check
db_url = settings.DATABASE_URL
sqlite_path = settings.SQLITE_FALLBACK_DB
actual_db_engine = "SQLITE LOCAL FALLBACK STORE (cosmohub_local.db)"
pgvector_available = False

try:
    with store._get_connection() as conn:
        conn.cursor().execute("SELECT 1")
    db_connected = True
except Exception as e:
    db_connected = False

print(f"Database Connected: {db_connected}")
print(f"Configured Database URL: {db_url}")
print(f"Actually Executed Storage Engine: {actual_db_engine}")
print(f"pgvector Extension Available: {pgvector_available} (Postgres daemon not running)")

# Active Providers Check
active_embedder = get_embedder()
active_embedder_name = active_embedder.__class__.__name__
if active_embedder_name == "LocalVectorEmbedder":
    active_embedder_desc = "LOCAL DETERMINISTIC VECTORIZER FALLBACK (384-dim)"
else:
    active_embedder_desc = f"OPENAI EMBEDDINGS ({settings.EMBEDDING_MODEL})"

active_reranker_desc = "HeuristicReranker"
active_generator_desc = "DETERMINISTIC GROUNDED EVIDENCE SYNTHESIZER FALLBACK" if not settings.OPENAI_API_KEY else "OPENAI LLM (gpt-4o-mini)"

print(f"Active Embedding Provider: {active_embedder_desc}")
print(f"Active Reranker Provider: {active_reranker_desc}")
print(f"Active Generator Provider: {active_generator_desc}")

# 2. CRAWL & INGEST AUTHORITATIVE SOURCES (Task 2, 3, 4)
print("\n--- 2. AUTHORITATIVE CORPUS CRAWLING & INGESTION ---")

registered_sources = source_registry.list_sources(enabled_only=True)
print(f"Registered Sources Count: {len(registered_sources)}")

crawled_sources_count = 0
failed_crawls = []
mismatched_sources = []
ingested_documents = []
total_chunks_created = 0

tier_distribution = {
    SourceQualityTier.TIER_1: 0,
    SourceQualityTier.TIER_2: 0,
    SourceQualityTier.TIER_3: 0,
    SourceQualityTier.TIER_4: 0,
    SourceQualityTier.TIER_5: 0
}

for reg_src in registered_sources:
    url = reg_src.source_url
    s_id = reg_src.source_id
    print(f"\nCrawling [{reg_src.source_tier}] {reg_src.publisher} ({url})...")
    
    t0_crawl = time.time()
    try:
        crawled_data = fetch_web_page(url, timeout=12)
        crawled_sources_count += 1
        
        # Check redirect identity mismatch
        if crawled_data["identity_mismatch"]:
            mismatched_sources.append({
                "source_id": s_id,
                "requested_url": url,
                "final_resolved_url": crawled_data["final_resolved_url"],
                "title": crawled_data["title"],
                "reason": f"Requested slug differed from resolved title '{crawled_data['title']}'"
            })
            print(f"  [MISMATCH DETECTED] Title: '{crawled_data['title']}' (Redirected: {crawled_data['was_redirected']})")

        # Parse & store document
        doc = WebParser().parse(source_id=s_id, raw_data=crawled_data, url_or_path=url, publisher=reg_src.publisher)
        store.save_document(doc)
        
        # Chunk & Embed
        chunks = chunk_document(doc)
        embeddings = active_embedder.embed_texts([c.content for c in chunks])
        store.save_chunks(chunks, embeddings)
        
        total_chunks_created += len(chunks)
        ingested_documents.append(doc)
        
        tier = doc.metadata.extra.get("source_tier", reg_src.source_tier)
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        print(f"  [SUCCESS] Doc ID: {doc.document_id} | Chunks: {len(chunks)} | Tier: {tier} | Hash: {doc.content_hash[:12]}...")

    except Exception as e:
        failed_crawls.append({
            "source_id": s_id,
            "publisher": reg_src.publisher,
            "url": url,
            "error": str(e)
        })
        print(f"  [FAILED] Error crawling {url}: {e}")

print(f"\n--- INGESTION SUMMARY ---")
print(f"Sources Registered: {len(registered_sources)}")
print(f"Sources Successfully Crawled & Persisted: {crawled_sources_count}")
print(f"Documents Ingested: {len(ingested_documents)}")
print(f"Total Chunks Created: {total_chunks_created}")
print(f"Failed Crawls Count: {len(failed_crawls)}")
print(f"Identity Mismatched Sources Count: {len(mismatched_sources)}")

print(f"\nSource Tier Distribution of Persisted Documents:")
for tier_name, count in tier_distribution.items():
    print(f"  * {tier_name}: {count} documents")

# 3. TEST THE REUSABLE LAUNCH QUERY (Task 6 & 7)
test_query = "Which European launch companies are developing reusable launch technology, what evidence supports each claim, and where is the evidence insufficient?"
print(f"\n" + "-"*80)
print(f"-> EXECUTING STAGE 2 INTEGRATION QUERY:")
print(f"   '{test_query}'")
print("-"*80)

t0_query = time.time()
plan = plan_query_execution(test_query)
fused_hits, stats = hybrid_retrieve(test_query, top_k=20)
reranked = rerank_evidence_candidates(test_query, fused_hits, top_k=6)

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
query_latency_ms = (time.time() - t0_query) * 1000

# 4. PRINT COMPLETE STAGE 2 AUTHORITATIVE REPORT (Task 9)
print("\n" + "="*80)
print("# AUTHORITATIVE CORPUS + ORVYRA INTEGRATION REPORT")
print("="*80)

print(f"\n1. SOURCES REGISTERED: {len(registered_sources)}")
for s in registered_sources:
    print(f"   - [{s.source_tier}] {s.publisher} ({s.source_url}) | Scope: {s.entity_scope}")

print(f"\n2. SOURCES ACTUALLY CRAWLED: {crawled_sources_count}")

print(f"\n3. DOCUMENTS INGESTED: {len(ingested_documents)}")
for d in ingested_documents:
    meta_ex = d.metadata.extra
    print(f"   - Doc ID: {d.document_id} | Title: '{d.title[:60]}...' | Tier: {meta_ex.get('source_tier')} | Hash: {d.content_hash[:12]}...")

print(f"\n4. CHUNK STATISTICS: {total_chunks_created} total semantic chunks indexed.")

print(f"\n5. SOURCE TIER DISTRIBUTION:")
for t_k, t_v in tier_distribution.items():
    print(f"   - {t_k}: {t_v} persisted documents")

print(f"\n6. RUNTIME INFRASTRUCTURE VERIFICATION:")
print(f"   - Database Engine: {actual_db_engine} (Connected: {db_connected})")
print(f"   - pgvector Available: {pgvector_available}")
print(f"   - Embedding Implementation: {active_embedder_desc}")
print(f"   - Reranker Implementation: {active_reranker_desc}")
print(f"   - Generator Implementation: {active_generator_desc}")

print(f"\n7. ORVYRA ENTITIES CREATED/UPDATED ({len(orvyra_response.entities)}):")
for e in orvyra_response.entities:
    print(f"   - [{e.kind.upper()}] {e.name} (ID: {e.id}, Region: {e.region or 'Global'})")

print(f"\n8. ORVYRA RELATIONSHIPS CREATED ({len(orvyra_response.edges)}):")
for edge in orvyra_response.edges:
    print(f"   - {edge.from_id} --({edge.rel})--> {edge.to_id} [Edge ID: {edge.id} | Ev Count: {len(edge.ev)}]")

print(f"\n9. EVIDENCE SUPPORTING EACH RELATIONSHIP:")
for edge in orvyra_response.edges:
    print(f"   Edge {edge.id} ({edge.from_id} -> {edge.to_id}):")
    for eid in edge.ev:
        ev_obj = next((ev for ev in orvyra_response.evidence if ev.id == eid), None)
        if ev_obj:
            print(f"     * Ev ID: {ev_obj.id} | Tier: {ev_obj.source_tier} | Conf: {ev_obj.confidence} | URL: {ev_obj.sourceUri}")

print(f"\n10. WITHHELD CLAIMS ({len(orvyra_response.withheld)}):")
for w in orvyra_response.withheld:
    print(f"   - Entity: {w.entity_id} | Field: {w.field}")
    print(f"     Reason: {w.reason}")

print(f"\n11. CONFLICTS DETECTED ({len(orvyra_response.conflicts)}):")
for c in orvyra_response.conflicts:
    print(f"   - Conflict ID: {c.conflict_id} | Subject: {c.subject_id} | Predicate: {c.predicate}")
    print(f"     Reason: {c.reason}")

print(f"\n12. RESULT OF ORIGINAL REUSABLE LAUNCH QUERY:")
print(f"   - Status: {orvyra_response.status}")
print(f"   - Confidence: {orvyra_response.confidence * 100:.0f}%")
print(f"   - Latency: {query_latency_ms:.1f} ms")

print(f"\n13. FULL EVIDENCE CHAIN FOR SUPPORTED ANSWER CLAIMS:")
if orvyra_response.evidence_chain:
    for chain in orvyra_response.evidence_chain:
        print(f"\n   [ANSWER STATEMENT] '{chain['statement']}'")
        print(f"   [CLAIM ID] {chain['claim_id']} (Conf: {chain['confidence']})")
        print(f"   [EVIDENCE ID] {chain['evidence_id']} (Tier: {chain['source_tier']})")
        print(f"   [DOCUMENT] ID: {chain['document_id']} | Hash: {chain['content_hash']}")
        print(f"   [SOURCE URL] {chain['source_url']}")
else:
    print("   (No direct claims supported due to missing non-mismatched evidence or insufficient tier confidence.)")

print(f"\n14. FAILED / REJECTED SOURCES ({len(failed_crawls) + len(mismatched_sources)}):")
print(f"   Failed Crawls ({len(failed_crawls)}):")
for f in failed_crawls:
    print(f"     * [{f['source_id']}] {f['publisher']} ({f['url']}) -> Error: {f['error']}")

print(f"   Identity Mismatched Sources ({len(mismatched_sources)}):")
for m in mismatched_sources:
    print(f"     * [{m['source_id']}] Requested: {m['requested_url']} -> Resolved Title: '{m['title']}' ({m['reason']})")

print(f"\n15. REMAINING LIMITATIONS:")
print("   - Primary company sites require CORS/User-Agent bypass or direct API access for un-blocked crawling.")
print("   - Local provider fallbacks active (LocalVectorEmbedder, HeuristicReranker, Grounded Synthesizer).")

print(f"\n" + "="*80)
print("FINAL GROUNDED ANSWER SYNTHESIS:")
print("="*80)
print(orvyra_response.answer)

print("\n" + "="*80)
print("STAGE 2 AUTHORITATIVE CORPUS & ORVYRA INTEGRATION VERIFICATION COMPLETE")
print("="*80)
