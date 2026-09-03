from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import DocumentSchema
from app.services.store import store

router = APIRouter()

@router.get("/documents", response_model=List[DocumentSchema])
def list_indexed_documents():
    return store.list_documents()

@router.get("/documents/{document_id}", response_model=DocumentSchema)
def get_document_by_id(document_id: str):
    doc = store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    return doc
