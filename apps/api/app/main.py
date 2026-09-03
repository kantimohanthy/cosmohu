import os
import uuid
import glob
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models.schemas import Source, SourceType, SourceStatus, Entity
from app.services.store import store
from app.services.parsers import parse_document
from app.services.chunker import chunk_document
from app.services.embedder import get_embedder

from app.api import query, search, sources, documents, evidence, entities, ingestion, eval, research

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API V1 Routers
api_v1_router = FastAPI()
app.include_router(research.router, prefix="/api", tags=["research"])
app.include_router(research.router, prefix=settings.API_V1_STR, tags=["research"])
app.include_router(query.router, prefix=settings.API_V1_STR, tags=["query"])
app.include_router(search.router, prefix=settings.API_V1_STR, tags=["search"])
app.include_router(sources.router, prefix=settings.API_V1_STR, tags=["sources"])
app.include_router(documents.router, prefix=settings.API_V1_STR, tags=["documents"])
app.include_router(evidence.router, prefix=settings.API_V1_STR, tags=["evidence"])
app.include_router(entities.router, prefix=settings.API_V1_STR, tags=["entities"])
app.include_router(ingestion.router, prefix=settings.API_V1_STR, tags=["ingestion"])
app.include_router(eval.router, prefix=settings.API_V1_STR, tags=["eval"])

@app.get("/")
def root():
    return {
        "engine": "CosmoHub Intelligence Engine",
        "version": "1.0.0",
        "status": "operational",
        "docs": f"{settings.API_V1_STR}/docs"
    }

@app.on_event("startup")
def seed_initial_knowledge_base():
    """Initializes and ingests grounded space economy seed datasets on first startup."""
    existing_sources = store.list_sources()
    if existing_sources:
        return  # Knowledge base already seeded

    print("[CosmoHub Engine] Seeding initial European Space Economy Knowledge Base...")

    # Seed files
    seed_files = [
        ("src_launch_companies", "European Launch Companies Dataset 2026", SourceType.CSV, "data/seed_sources/launch_companies_europe.csv", "CosmoHub Space Research Observatory"),
        ("src_space_missions", "Space Infrastructure & Missions Registry", SourceType.JSON, "data/seed_sources/space_missions_funding.json", "EUSPA / European Union"),
        ("src_policy_briefing", "ESA Policy & Micro-Launcher Briefing 2026", SourceType.MARKDOWN, "data/seed_sources/esa_euspa_briefings.md", "European Space Agency (ESA)"),
    ]

    embedder = get_embedder()

    for s_id, s_name, s_type, s_path, s_pub in seed_files:
        full_path = os.path.abspath(s_path)
        if not os.path.exists(full_path):
            continue

        src = Source(
            source_id=s_id,
            name=s_name,
            source_type=s_type,
            url_or_path=full_path,
            status=SourceStatus.ACTIVE,
            trust_level=0.98,
            last_crawled_at=datetime.utcnow(),
            last_success_at=datetime.utcnow()
        )
        store.save_source(src)

        # Parse & Chunk
        doc = parse_document(source_id=s_id, source_type=s_type, raw_data=full_path, url_or_path=full_path, publisher=s_pub)
        src.last_content_hash = doc.content_hash
        store.save_document(doc)

        chunks = chunk_document(doc)
        texts = [c.content for c in chunks]
        embeddings = embedder.embed_texts(texts)
        store.save_chunks(chunks, embeddings)

        src.document_count = 1
        store.save_source(src)

    # Seed Space Entities
    seed_entities = [
        Entity(
            entity_id="ent_isar",
            name="Isar Aerospace",
            entity_type="Company",
            country="Germany",
            funding_raised_eur_m=310.0,
            key_technologies=["Spectrum Rocket", "Aquila Engine", "Carbon Fiber Cryo-Tanks"],
            description="Lead German small-launch manufacturer developing two-stage Spectrum rocket for LEO orbit delivery.",
            sources_count=3
        ),
        Entity(
            entity_id="ent_rfa",
            name="Rocket Factory Augsburg (RFA)",
            entity_type="Company",
            country="Germany",
            funding_raised_eur_m=85.0,
            key_technologies=["RFA ONE", "Staged Combustion Engine", "Helix Engine"],
            description="Commercial launcher developer deploying high-volume automated orbital rocket manufacturing.",
            sources_count=3
        ),
        Entity(
            entity_id="ent_maiaspace",
            name="MaiaSpace",
            entity_type="Company",
            country="France",
            funding_raised_eur_m=125.0,
            key_technologies=["Maia Reusable Launcher", "Prometheus Engine", "Bio-Methane"],
            description="ArianeGroup subsidiary pioneering reusable light launcher technology.",
            sources_count=2
        ),
        Entity(
            entity_id="ent_pld",
            name="PLD Space",
            entity_type="Company",
            country="Spain",
            funding_raised_eur_m=140.0,
            key_technologies=["Miura 1", "Miura 5", "TEP-1 Engine"],
            description="Spanish commercial orbital transport developer, first private European company to launch a suborbital rocket.",
            sources_count=3
        ),
        Entity(
            entity_id="ent_iris2",
            name="IRIS² Satellite Constellation",
            entity_type="Constellation",
            country="European Union",
            funding_raised_eur_m=6000.0,
            key_technologies=["Multi-orbit LEO/MEO", "Quantum Encrypted Downlinks", "Government Broadband"],
            description="Sovereign European secure telecommunications constellation providing resilient broadband.",
            sources_count=4
        )
    ]

    for ent in seed_entities:
        store.save_entity(ent)

    print("[CosmoHub Engine] Knowledge base initialized successfully with 3 sources and 5 space entities.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
