"""
Player management router.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.firebase_client import get_db

router = APIRouter(prefix="/api", tags=["players"])


class RegisterRequest(BaseModel):
    display_name: str


@router.get("/players")
async def list_players():
    """List all player slots."""
    db = get_db()
    players = []
    for doc in db.collection("athletes").stream():
        data = doc.to_dict()
        players.append(
            {
                "id": doc.id,
                "display_name": data.get("display_name"),
                "strava_athlete_id": data.get("strava_athlete_id"),
                "status": data.get("status"),
                "profile_photo": data.get("profile_photo"),
                "strava_firstname": data.get("strava_firstname"),
                "strava_lastname": data.get("strava_lastname"),
            }
        )
    return {"players": players}


@router.post("/register")
async def register_player(req: RegisterRequest):
    """Admin: create a new player slot."""
    db = get_db()

    # Auto-generate player ID
    existing = list(db.collection("athletes").stream())
    player_id = f"player_{len(existing) + 1}"

    db.collection("athletes").document(player_id).set(
        {
            "display_name": req.display_name,
            "strava_athlete_id": None,
            "status": "pending",
            "profile_photo": None,
            "access_token": None,
            "refresh_token": None,
            "token_expiry": None,
        }
    )

    return {"player_id": player_id, "display_name": req.display_name, "status": "pending"}
