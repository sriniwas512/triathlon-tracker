"""
Scores router — calculate, retrieve, and dashboard aggregation.
"""
from fastapi import APIRouter, HTTPException
from firebase_client import get_db
from services.scoring_service import (
    calculate_block_scores,
    get_all_scores,
    get_dashboard_data,
)
from services.block_service import get_most_recently_closed_block, get_all_blocks

router = APIRouter(prefix="/api", tags=["scores"])


@router.post("/scores/calculate/{block_id}")
async def calculate_scores(block_id: str):
    """Manually trigger scoring for a specific block."""
    try:
        result = calculate_block_scores(block_id)
        return {"status": "ok", "scores": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scores/calculate-job")
async def calculate_job():
    """
    Scheduled job endpoint: score the most recently closed block.
    Called every Monday 12:00 UTC by Cloud Scheduler.
    """
    block = get_most_recently_closed_block()
    if block is None:
        return {"status": "no_block", "message": "No unlocked closed blocks to score"}

    try:
        result = calculate_block_scores(block["block_id"])
        return {"status": "ok", "block_id": block["block_id"], "scores": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scores")
async def list_scores():
    """Retrieve all scored blocks."""
    scores = get_all_scores()
    return {"scores": scores}


@router.get("/scores/{block_id}")
async def get_score(block_id: str):
    """Retrieve score for a specific block."""
    db = get_db()
    doc = db.collection("scores").document(block_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Score not found for this block")
    return doc.to_dict()


@router.get("/dashboard")
async def dashboard():
    """Aggregated dashboard data for all panels."""
    data = get_dashboard_data()
    return data


@router.get("/blocks")
async def list_blocks():
    """List all blocks with their status."""
    blocks = get_all_blocks()
    return {"blocks": blocks}
