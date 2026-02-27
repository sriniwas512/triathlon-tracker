"""
Admin router for development and testing utilities.
"""
from fastapi import APIRouter
from firebase_client import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.delete("/reset")
async def reset_data():
    """
    Reset all athlete data, activities, and scores for testing.
    - Deletes all docs in 'athletes', 'activities', 'scores'.
    - Re-creates player_1 and player_2 with status 'disconnected'.
    """
    db = get_db()

    # 1. Clear collections
    for collection_name in ["athletes", "activities", "scores"]:
        coll_ref = db.collection(collection_name)
        docs = coll_ref.stream()
        for doc in docs:
            doc.reference.delete()

    # 2. Reset player slots
    player_slots = [
        {"id": "player_1", "name": "Player 1"},
        {"id": "player_2", "name": "Player 2"},
    ]

    for p in player_slots:
        db.collection("athletes").document(p["id"]).set(
            {
                "display_name": p["name"],
                "strava_athlete_id": None,
                "status": "disconnected",
                "profile_photo": None,
                "access_token": None,
                "refresh_token": None,
                "token_expiry": None,
                "strava_firstname": None,
                "strava_lastname": None,
            }
        )

    return {"message": "All athlete data, activities, and scores have been cleared and player slots reset."}
