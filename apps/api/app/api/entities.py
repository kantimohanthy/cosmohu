from fastapi import APIRouter
from typing import List
from app.models.schemas import Entity
from app.services.store import store

router = APIRouter()

@router.get("/entities", response_model=List[Entity])
def list_space_entities():
    return store.list_entities()
