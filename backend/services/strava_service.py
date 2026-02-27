"""
Strava API service — OAuth, token refresh, activity fetching.
"""
import time
import httpx
from config import (
    STRAVA_CLIENT_ID,
    STRAVA_CLIENT_SECRET,
    STRAVA_TOKEN_URL,
    STRAVA_API_BASE,
)
from firebase_client import get_db


async def exchange_code(code: str) -> dict:
    """Exchange authorization code for tokens + athlete info."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(player_id: str) -> str:
    """Refresh the Strava access token for a player. Returns new access token."""
    db = get_db()
    doc = db.collection("athletes").document(player_id).get()
    if not doc.exists:
        raise ValueError(f"Player {player_id} not found")

    player_data = doc.to_dict()
    token_expiry = player_data.get("token_expiry", 0)

    # If token still valid for > 5 minutes, reuse it
    if token_expiry > time.time() + 300:
        return player_data["access_token"]

    # Refresh
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": player_data["refresh_token"],
            },
        )
        resp.raise_for_status()
        data = resp.json()

    # Update Firestore
    db.collection("athletes").document(player_id).update(
        {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "token_expiry": data["expires_at"],
        }
    )

    return data["access_token"]


async def get_athlete_profile(access_token: str) -> dict:
    """GET /athlete — returns authenticated athlete profile."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{STRAVA_API_BASE}/athlete",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def list_activities(
    access_token: str, after_ts: int, before_ts: int
) -> list[dict]:
    """
    GET /athlete/activities with pagination.
    Returns list of SummaryActivity objects.
    """
    all_activities = []
    page = 1
    per_page = 100

    async with httpx.AsyncClient() as client:
        while True:
            resp = await client.get(
                f"{STRAVA_API_BASE}/athlete/activities",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "after": after_ts,
                    "before": before_ts,
                    "page": page,
                    "per_page": per_page,
                },
            )
            resp.raise_for_status()
            activities = resp.json()
            if not activities:
                break
            all_activities.extend(activities)
            if len(activities) < per_page:
                break
            page += 1

    return all_activities


async def get_recent_activities(access_token: str, count: int = 5) -> list[dict]:
    """GET /athlete/activities — returns the N most recent activities."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{STRAVA_API_BASE}/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "per_page": count,
                "page": 1,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_activity_detail(access_token: str, activity_id: int) -> dict:
    """GET /activities/{id} — returns DetailedActivity with calories."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{STRAVA_API_BASE}/activities/{activity_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
