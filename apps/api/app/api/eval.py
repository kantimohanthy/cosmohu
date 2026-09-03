from fastapi import APIRouter
from app.services.eval import run_evaluation_suite

router = APIRouter()

@router.get("/eval")
def get_evaluation_results():
    return run_evaluation_suite()

@router.post("/eval")
def trigger_evaluation_suite():
    return run_evaluation_suite()
