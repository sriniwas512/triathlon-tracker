"""
Authentication router — Strava OAuth 2.0 flow.
"""
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Query
from config import (
    STRAVA_CLIENT_ID,
    STRAVA_AUTH_URL,
    BACKEND_URL,
    FRONTEND_URL,
)
from firebase_client import get_db
from services.strava_service import exchange_code, get_athlete_profile

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/strava")
async def strava_login(player_id: str = Query(...)):
    """
    Redirect to Strava OAuth authorization page.
    Pass player_id in state so we can bind on callback.
    """
    params = {
        "client_id": STRAVA_CLIENT_ID,
        "redirect_uri": f"{BACKEND_URL}/api/auth/callback",
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "activity:read_all,profile:read_all",
        "state": player_id,
    }
    url = f"{STRAVA_AUTH_URL}?{urlencode(params)}"
    return {"redirect_url": url}


@router.get("/callback")
async def strava_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
):
    """
    Strava OAuth callback. Exchange code for tokens, bind to player slot.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    player_id = state
    db = get_db()

    # Verify player slot exists
    player_ref = db.collection("athletes").document(player_id)
    player_doc = player_ref.get()
    if not player_doc.exists:
        raise HTTPException(
            status_code=404,
            detail="No player slot found for this request",
        )

    # Exchange code for tokens
    token_data = await exchange_code(code)
    athlete_info = token_data.get("athlete", {})
    strava_id = str(athlete_info.get("id", ""))

    # Check if this Strava account is already bound to a different slot
    existing_query = (
        db.collection("athletes")
        .where("strava_athlete_id", "==", strava_id)
        .stream()
    )
    for edoc in existing_query:
        if edoc.id != player_id:
            raise HTTPException(
                status_code=409,
                detail="No player slot found for this Strava account",
            )

    # Check if this slot already has a different Strava ID bound
    current_data = player_doc.to_dict()
    if (
        current_data.get("strava_athlete_id")
        and current_data["strava_athlete_id"] != strava_id
    ):
        raise HTTPException(
            status_code=409,
            detail="This player slot is bound to a different Strava account",
        )

    # Get profile info
    profile_photo = athlete_info.get("profile", athlete_info.get("profile_medium", ""))
    fname = athlete_info.get("firstname", "")
    lname = athlete_info.get("lastname", "")
    full_name = f"{fname} {lname}".strip() or "Athlete"

    # Update player document
    player_ref.update(
        {
            "display_name": full_name,
            "strava_athlete_id": strava_id,
            "status": "connected",
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "token_expiry": token_data["expires_at"],
            "profile_photo": profile_photo,
            "strava_firstname": fname,
            "strava_lastname": lname,
        }
    )

    # Redirect to frontend
    return {"status": "connected", "redirect": f"{FRONTEND_URL}/login?connected={player_id}"}


@router.get("/status")
async def auth_status():
    """Check if all players are connected."""
    db = get_db()
    players = []
    all_connected = True

    for doc in db.collection("athletes").stream():
        data = doc.to_dict()
        connected = data.get("status") == "connected"
        if not connected:
            all_connected = False
        players.append(
            {
                "id": doc.id,
                "display_name": data.get("display_name"),
                "status": data.get("status"),
                "profile_photo": data.get("profile_photo"),
                "strava_firstname": data.get("strava_firstname"),
                "strava_lastname": data.get("strava_lastname"),
            }
        )

    return {"all_connected": all_connected, "players": players}
