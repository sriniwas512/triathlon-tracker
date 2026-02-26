"""
Activity sync service — fetches activities from Strava, filters, maps,
assigns to blocks, and stores in Firestore.
"""
from datetime import datetime, timezone
from backend.config import (
    BLOCK_DEFINITIONS,
    get_block_for_activity,
    get_sport_category,
)
from backend.firebase_client import get_db
from backend.services.strava_service import (
    refresh_access_token,
    list_activities,
    get_activity_detail,
)


async def sync_player_activities(player_id: str) -> dict:
    """
    Sync Strava activities for a player across all block windows.
    Returns summary of synced activities.
    """
    db = get_db()
    access_token = await refresh_access_token(player_id)

    player_doc = db.collection("athletes").document(player_id).get()
    if not player_doc.exists:
        raise ValueError(f"Player {player_id} not found")

    player_data = player_doc.to_dict()
    strava_athlete_id = player_data.get("strava_athlete_id")

    synced = {"new": 0, "skipped": 0, "ignored_sport": 0}

    for block in BLOCK_DEFINITIONS:
        # Check if block is locked — don't re-sync locked blocks
        block_doc = db.collection("blocks").document(block["block_id"]).get()
        if block_doc.exists and block_doc.to_dict().get("locked", False):
            continue

        after_ts = int(block["window_open_utc"].timestamp())
        before_ts = int(block["window_close_utc"].timestamp())

        # List activities in this window
        activities = await list_activities(access_token, after_ts, before_ts)

        for activity in activities:
            activity_id = str(activity["id"])

            # Check if already stored
            existing = db.collection("activities").document(activity_id).get()
            if existing.exists:
                synced["skipped"] += 1
                continue

            # Map sport type
            sport_type = activity.get("sport_type", "")
            sport_category = get_sport_category(sport_type)
            if sport_category is None:
                synced["ignored_sport"] += 1
                continue

            # Check sport is valid for this block
            if sport_category not in block["sports"]:
                synced["ignored_sport"] += 1
                continue

            # Parse start_date
            start_date_str = activity.get("start_date", "")
            start_date_utc = datetime.fromisoformat(
                start_date_str.replace("Z", "+00:00")
            )

            # Verify it falls within block window
            assigned_block = get_block_for_activity(start_date_utc)
            if assigned_block != block["block_id"]:
                synced["skipped"] += 1
                continue

            # Fetch detailed activity for calories
            detail = await get_activity_detail(access_token, activity["id"])
            calories = detail.get("calories", 0) or 0
            kilojoules = detail.get("kilojoules", 0) or 0

            # Fallback: derive calories from kilojoules
            if calories == 0 and kilojoules > 0:
                calories = round(kilojoules * 0.239, 2)

            # Store
            db.collection("activities").document(activity_id).set(
                {
                    "activity_id": activity_id,
                    "player_id": player_id,
                    "strava_athlete_id": strava_athlete_id,
                    "sport_type": sport_type,
                    "sport_category": sport_category,
                    "block_id": block["block_id"],
                    "start_date_utc": start_date_utc.isoformat(),
                    "calories": calories,
                    "kilojoules": kilojoules,
                    "distance_meters": activity.get("distance", 0) or 0,
                    "moving_time_seconds": activity.get("moving_time", 0) or 0,
                    "name": activity.get("name", ""),
                }
            )
            synced["new"] += 1

    return synced
