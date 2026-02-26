"""
Activities router — sync from Strava, list stored activities.
"""
from fastapi import APIRouter, HTTPException
from firebase_client import get_db
from services.sync_service import sync_player_activities

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.post("/sync/{player_id}")
async def sync_activities(player_id: str):
    """Fetch and store activities from Strava for a player."""
    db = get_db()
    player_doc = db.collection("athletes").document(player_id).get()
    if not player_doc.exists:
        raise HTTPException(status_code=404, detail="Player not found")
    if player_doc.to_dict().get("status") != "connected":
        raise HTTPException(status_code=400, detail="Player not connected to Strava")

    try:
        result = await sync_player_activities(player_id)
        return {"status": "ok", "synced": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all")
async def sync_all_activities():
    """Sync activities for all connected players."""
    db = get_db()
    results = {}
    for doc in db.collection("athletes").stream():
        data = doc.to_dict()
        if data.get("status") == "connected":
            try:
                result = await sync_player_activities(doc.id)
                results[doc.id] = result
            except Exception as e:
                results[doc.id] = {"error": str(e)}
    return {"status": "ok", "results": results}


@router.get("/{player_id}")
async def list_activities(player_id: str):
    """List all stored activities for a player."""
    db = get_db()
    activities = []
    query = db.collection("activities").where("player_id", "==", player_id).stream()
    for doc in query:
        activities.append(doc.to_dict())

    # Sort by start date
    activities.sort(key=lambda a: a.get("start_date_utc", ""))
    return {"activities": activities}
