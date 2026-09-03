# COSMOHUB — INTELLIGENCE ENGINE

> **Intelligence Infrastructure for the Space Economy**

CosmoHub Intelligence Engine is a grounded AI research system, space-economy intelligence platform, evidence explorer, and modern data terminal.

---

## Core Principle

**THE LLM IS NOT THE SOURCE OF TRUTH.**

The source of truth is the underlying evidence and knowledge infrastructure. The LLM is a reasoning and interface layer over that infrastructure.

**NO EVIDENCE → NO CLAIM.**

If sufficient evidence cannot be found, the system explicitly reports `INSUFFICIENT_EVIDENCE`.

## Architecture & Intelligence Workspace (Stage 4.3)

The web frontend (`apps/web`) is a **Three-Column Intelligence Workspace** consuming live REST Session APIs:

```text
INVESTIGATION SESSION (POST /api/v1/research/sessions)
  ↓
MULTI-QUERY ACCUMULATION (POST /api/v1/research/sessions/{id}/queries)
  ↓
QUERY PLANNER → RETRIEVAL → RERANKING → SEMANTIC VERIFIER
  ↓
ORVYRA KNOWLEDGE GRAPH
  ↓
SESSION ARTIFACT ACCUMULATION (propositions, claims, evidence, sources, insufficiency, conflicts)
  ↓
THREE-COLUMN INTELLIGENCE WORKSPACE
┌───────────────────────────┬────────────────────────────────┬───────────────────────────┐
│ LEFT: INVESTIGATION       │ CENTER: MAIN WORKSPACE         │ RIGHT: EVIDENCE EXPLORER  │
│ - Session Title & Switcher│ - Multi-Query Workspace        │ - Canonical Node Chain    │
│ - Queries & Discovered    │ - Entity Comparison Matrix     │   PROPOSITION -> CLAIM    │
│   Entities List           │ - 2D Relationship Knowledge    │   -> EVIDENCE -> CHUNK    │
│ - Evidence & Source Counts│   Graph (SVG Canvas)           │   -> DOCUMENT -> SOURCE   │
│ - Density Metric Bar      │ - Copy Research Summary        │ - Verbatim Passages       │
└───────────────────────────┴────────────────────────────────┴───────────────────────────┘
```

### Research Session Endpoints (Stage 4.3)
- `POST /api/v1/research/sessions` — Create a new investigation session.
- `GET /api/v1/research/sessions` — List all investigation sessions.
- `GET /api/v1/research/sessions/{session_id}` — Retrieve full session details & aggregated artifacts.
- `POST /api/v1/research/sessions/{session_id}/queries` — Add research query to session and run pipeline.
- `DELETE /api/v1/research/sessions/{session_id}` — Delete investigation session.
- **Inspectable Evidence Chains**: Clicking **"WHY THIS CONCLUSION?"** displays the 6-step canonical lineage ($\text{PROPOSITION} \rightarrow \text{CLAIM} \rightarrow \text{EVIDENCE} \rightarrow \text{CHUNK} \rightarrow \text{DOCUMENT} \rightarrow \text{SOURCE}$) with verbatim passage quotes and 5-dimension entailment checks.

---

## API Contract (Stage 4.0 & Stage 4.1)

### 1. Research Pipeline Query Endpoint
`POST /api/research` or `POST /api/v1/research`

**Request Payload**:
```json
{
  "query": "Which European launch companies are developing reusable launch vehicles?"
}
```

**Response Payload**:
```json
{
  "query": "Which European launch companies are developing reusable launch vehicles?",
  "status": "COMPLETED",
  "run_id": "e2e_run_1788390000",
  "answer": "PLD Space is actively developing reusable launch vehicle technology...",
  "propositions": [
    {
      "proposition_id": "PROP-PLD-REUSABLE-001",
      "entity_id": "pld",
      "entity_name": "PLD Space",
      "predicate": "develops",
      "object": "reusable_launch_vehicle",
      "status": "SUPPORTED",
      "temporal_scope": "IN_DEVELOPMENT",
      "evidence_strength": 0.95,
      "evidence_ids": ["ev_chk_miura5_spec"],
      "claim_id": "clm_pld_reusable",
      "relationship_id": "rel_pld_reusable"
    }
  ],
  "claims": [...],
  "evidence": [...],
  "insufficient": [...],
  "conflicts": [],
  "withheld": [],
  "sources": [...],
  "metadata": {
    "planning_ms": 2.35,
    "retrieval_ms": 5.48,
    "reranking_ms": 3.92,
    "verification_ms": 4.70,
    "orchestration_ms": 1.57,
    "synthesis_ms": "NOT_MEASURED",
    "validation_ms": 0.08,
    "total_ms": 18.05,
    "provider_type": "DETERMINISTIC_FALLBACK"
  }
}
```

### 2. "WHY THIS CONCLUSION?" Evidence Chain Endpoint
`GET /api/research/{proposition_id}/evidence` or `GET /api/v1/research/{proposition_id}/evidence`

**Response Payload**:
```json
{
  "proposition_id": "PROP-PLD-REUSABLE-001",
  "entity_id": "pld",
  "entity_name": "PLD Space",
  "predicate": "develops",
  "object": "reusable_launch_vehicle",
  "status": "SUPPORTED",
  "evidence_chain": [
    {"step": 1, "type": "PROPOSITION", "id": "PROP-PLD-REUSABLE-001", "label": "PLD Space develops reusable_launch_vehicle"},
    {"step": 2, "type": "CLAIM", "id": "clm_pld_reusable", "label": "PLD Space is developing MIURA 5 reusable launcher"},
    {"step": 3, "type": "EVIDENCE", "id": "ev_chk_miura5_spec", "text": "PLD Space is developing MIURA 5...", "source_tier": "TIER_1"},
    {"step": 4, "type": "CHUNK", "id": "chk_miura5_spec_0", "document_id": "doc_pld_miura5_spec"},
    {"step": 5, "type": "DOCUMENT", "id": "doc_pld_miura5_spec", "title": "PLD Space MIURA 5 Overview", "content_hash": "hash_pld_miura5_spec"},
    {"step": 6, "type": "SOURCE", "id": "src_pld_official", "publisher": "PLD Space Official", "url": "https://www.pldspace.com/en/miura-5.html"}
  ]
}
```

---

## Architectural Highlights

- **Multi-Format Ingestion**: Web crawling with strict SSRF guards, PDFs, CSV, JSON, Markdown, and DOCX parsers normalizing heterogeneous input into canonical document representations.
- **Incremental Processing & Content Hashing**: SHA-256 deduplication and change detection. Unchanged content is skipped; updated content is re-indexed idempotently.
- **Hybrid Retrieval Engine**: Dense vector cosine similarity search + Sparse BM25 keyword matching fused via **Reciprocal Rank Fusion (RRF)**.
- **Entity-Aware Cross-Encoder Reranking**: Reranks top candidates with generalizable entity matching boost, domain predicate preservation, and source tier weighting.
- **5-Dimension Semantic Verification**: Entailment verifier validating Entity Attribution, Predicate Support, Object Support, Temporal Scope, and Semantic Completeness (`NO ENTAILMENT → NO CLAIM`).
- **Prompt Injection Defense**: External text retrieved from external sources is treated strictly as static DATA and enclosed within data blocks. Instructions embedded inside crawled content are ignored.
- **Dual Vector Engine**: Scalable PostgreSQL + `pgvector` for production & lightweight local SQLite + vector index for immediate zero-dependency local execution out of the box.
- **Evaluation Suite**: Built-in benchmark suite to evaluate Recall@K, Groundedness, and reranking uplift across European space datasets.

---

## Quick Start (Local Standalone Execution)

### 1. Backend API (FastAPI)
```bash
cd apps/api
python -m venv venv
venv\Scripts\activate  # Windows: venv\Scripts\activate | Unix: source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```
*API running at `http://localhost:8000`. OpenAPI docs available at `http://localhost:8000/api/v1/docs`.*

### 2. Web Frontend (Next.js)
```bash
cd apps/web
npm install
npm run dev
```
*Interface running at `http://localhost:3000`.*

---

## Docker Production Deployment

```bash
docker compose up --build
```
*Launches PostgreSQL with pgvector, FastAPI API service, and Next.js Web App.*

---

## Grounded Space Datasets Included

- `launch_companies_europe.csv`: European small and medium launch providers (Isar Aerospace, Rocket Factory Augsburg, MaiaSpace, PLD Space, Orbex, HyImpulse, Avio, ArianeGroup).
- `space_missions_funding.json`: Multi-orbital satellite infrastructure, IRIS² constellation, Ariane 6, Copernicus expansion, and EAGLE-1 Quantum Key Distribution.
- `esa_euspa_briefings.md`: European Launcher Challenge policy briefing, spaceport infrastructure (Andøya, Sutherland, SaxaVord, Kourou), and micro-launcher capital dynamics.
