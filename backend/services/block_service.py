"""
Block management service — seeding, window lookups, lock management.
"""
from datetime import datetime, timezone
from backend.config import BLOCK_DEFINITIONS
from backend.firebase_client import get_db


def seed_blocks():
    """Seed block documents in Firestore if they don't exist."""
    db = get_db()
    for block in BLOCK_DEFINITIONS:
        doc_ref = db.collection("blocks").document(block["block_id"])
        if not doc_ref.get().exists:
            doc_ref.set(
                {
                    "block_id": block["block_id"],
                    "label": block["label"],
                    "window_open_utc": block["window_open_utc"].isoformat(),
                    "window_close_utc": block["window_close_utc"].isoformat(),
                    "sports": block["sports"],
                    "locked": False,
                    "calculated_at": None,
                }
            )


def seed_players(player_names: list[str]):
    """Seed player slots in Firestore if none exist."""
    db = get_db()
    athletes_ref = db.collection("athletes")
    existing = list(athletes_ref.stream())

    if len(existing) >= len(player_names):
        return  # Already seeded

    for i, name in enumerate(player_names):
        player_id = f"player_{i + 1}"
        doc_ref = athletes_ref.document(player_id)
        if not doc_ref.get().exists:
            doc_ref.set(
                {
                    "display_name": name,
                    "strava_athlete_id": None,
                    "status": "pending",
                    "profile_photo": None,
                    "access_token": None,
                    "refresh_token": None,
                    "token_expiry": None,
                }
            )


def get_most_recently_closed_block() -> dict | None:
    """
    Return the block definition whose window has closed most recently
    and is not yet locked. Returns None if no such block exists.
    """
    now = datetime.now(timezone.utc)
    db = get_db()

    candidates = []
    for block in BLOCK_DEFINITIONS:
        if block["window_close_utc"] < now:
            # Check if locked
            doc = db.collection("blocks").document(block["block_id"]).get()
            if doc.exists and not doc.to_dict().get("locked", False):
                candidates.append(block)

    if not candidates:
        return None

    # Return the one with the latest close time
    candidates.sort(key=lambda b: b["window_close_utc"], reverse=True)
    return candidates[0]


def get_all_blocks() -> list[dict]:
    """Return all blocks from Firestore."""
    db = get_db()
    blocks = []
    for doc in db.collection("blocks").stream():
        blocks.append(doc.to_dict())
    return blocks
