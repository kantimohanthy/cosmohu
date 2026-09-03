import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import Source, SourceCreate, SourceStatus
from app.services.store import store

router = APIRouter()

@router.get("/sources", response_model=List[Source])
def get_all_sources():
    return store.list_sources()

@router.post("/sources", response_model=Source)
def create_new_source(source_in: SourceCreate):
    source_id = f"src_{uuid.uuid4().hex[:12]}"
    source = Source(
        source_id=source_id,
        name=source_in.name,
        source_type=source_in.source_type,
        url_or_path=source_in.url_or_path,
        crawl_frequency=source_in.crawl_frequency,
        trust_level=source_in.trust_level,
        configuration=source_in.configuration,
        status=SourceStatus.IDLE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return store.save_source(source)

@router.get("/sources/{source_id}", response_model=Source)
def get_source_by_id(source_id: str):
    source = store.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")
    return source
