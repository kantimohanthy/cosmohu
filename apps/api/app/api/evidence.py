from fastapi import APIRouter, HTTPException
from app.models.schemas import EvidencePassage
from app.services.store import store

router = APIRouter()

@router.get("/evidence/{passage_id}")
def get_evidence_details(passage_id: str):
    """Retrieve full passage provenance & source metadata by passage ID."""
    # Chunk ID prefix match
    chunk_id = passage_id.replace("ev_", "chk_") if passage_id.startswith("ev_") else passage_id
    with store._get_connection() as conn:
        row = conn.cursor().execute("SELECT * FROM chunks WHERE chunk_id LIKE ?", (f"%{chunk_id}%",)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Evidence passage '{passage_id}' not found.")
        doc = store.get_document(row["document_id"])
        return {
            "passage_id": passage_id,
            "chunk_id": row["chunk_id"],
            "document": doc,
            "heading_context": row["heading_context"],
            "text": row["content"],
            "publisher": row["publisher"],
            "source_url": row["source_url"],
            "published_at": row["published_at"]
        }
