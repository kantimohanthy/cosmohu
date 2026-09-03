import uuid
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from app.models.schemas import IngestionJob, IngestionJobStatus, SourceStatus
from app.services.store import store
from app.services.parsers import parse_document
from app.services.chunker import chunk_document
from app.services.embedder import get_embedder
from app.services.hashing import compute_content_hash

router = APIRouter()

class TriggerIngestionRequest(BaseModel):
    source_id: str

def execute_ingestion_pipeline(job_id: str, source_id: str):
    """
    Executes complete end-to-end ingestion pipeline:
    DISCOVERY -> FETCH/CRAWL -> PARSE -> SANITIZE -> NORMALIZE -> VALIDATE -> HASH/DEDUP -> CHUNK -> EMBED -> INDEX -> PROVENANCE
    """
    job = store.get_job(job_id)
    if not job:
        return
        
    source = store.get_source(source_id)
    if not source:
        job.status = IngestionJobStatus.FAILED
        job.error_message = f"Source '{source_id}' not found."
        store.save_job(job)
        return

    try:
        job.status = IngestionJobStatus.RUNNING
        store.save_job(job)

        # Parse document
        doc = parse_document(
            source_id=source.source_id,
            source_type=source.source_type,
            raw_data=source.url_or_path,
            url_or_path=source.url_or_path,
            publisher=source.name
        )

        job.documents_discovered = 1
        job.bytes_ingested = len(doc.content.encode('utf-8'))

        # Check content hash for change detection
        if source.last_content_hash == doc.content_hash:
            # Unchanged content: Skip re-indexing!
            job.status = IngestionJobStatus.COMPLETED
            job.completed_at = datetime.utcnow().isoformat()
            job.content_changed = False
            job.documents_processed = 1
            store.save_job(job)
            return

        # Content changed or new source: Index document and chunks
        job.content_changed = True
        store.save_document(doc)

        # Chunk content
        chunks = chunk_document(doc)
        job.chunks_created = len(chunks)

        # Embed chunks
        embedder = get_embedder()
        texts = [c.content for c in chunks]
        embeddings = embedder.embed_texts(texts)

        # Index vectors in Store
        store.save_chunks(chunks, embeddings)

        # Update source metadata
        source.status = SourceStatus.ACTIVE
        source.last_crawled_at = datetime.utcnow()
        source.last_success_at = datetime.utcnow()
        source.last_content_hash = doc.content_hash
        source.document_count += 1
        source.updated_at = datetime.utcnow()
        store.save_source(source)

        job.status = IngestionJobStatus.COMPLETED
        job.completed_at = datetime.utcnow().isoformat()
        job.documents_processed = 1
        store.save_job(job)

    except Exception as e:
        job.status = IngestionJobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.utcnow().isoformat()
        store.save_job(job)

@router.post("/ingestion/jobs", response_model=IngestionJob)
def trigger_ingestion_job(req: TriggerIngestionRequest, background_tasks: BackgroundTasks):
    source = store.get_source(req.source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{req.source_id}' not found.")

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = IngestionJob(
        job_id=job_id,
        source_id=req.source_id,
        status=IngestionJobStatus.PENDING,
        started_at=datetime.utcnow().isoformat()
    )
    store.save_job(job)
    background_tasks.add_task(execute_ingestion_pipeline, job_id, req.source_id)
    return job

@router.get("/ingestion/jobs/{job_id}", response_model=IngestionJob)
def get_ingestion_job_status(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Ingestion job '{job_id}' not found.")
    return job
