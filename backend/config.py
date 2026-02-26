import os
print("DEBUG BACKEND_URL =", os.environ.get("API_BASE_URL"), flush=True)

"""
Configuration for the Triathlon Tracker backend.
Loads environment variables and defines block windows.
"""
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(override=False)

# --- Strava ---
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")
STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/api/v3/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"

# --- Firebase ---
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")

# --- Players ---
# Player names are now pulled from Strava.

# --- Display ---
TIMEZONE_DISPLAY = os.getenv("TIMEZONE_DISPLAY", "Asia/Singapore")

# --- URLs ---
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
# Railway uses API_BASE_URL for the backend endpoint as requested
BACKEND_URL = os.getenv("API_BASE_URL") or os.getenv("BACKEND_URL", "http://localhost:8000")

# --- Timezone helpers ---
JST = timezone(timedelta(hours=9))
PST = timezone(timedelta(hours=-8))

# --- Sport Type Mapping ---
VALID_SPORT_TYPES = {
    "Ride": "Cycling",
    "MountainBikeRide": "Cycling",
    "GravelRide": "Cycling",
    "Run": "Running",
    "TrailRun": "Running",
    "Swim": "Swimming",
}

# --- Block Definitions ---
# Each block: (block_id, label, window_open_utc, window_close_utc, sports_list)
# Opens: Friday 00:00 JST → UTC = Thurs 15:00 UTC (except Block 1)
# Closes: Sunday 23:59:59 PST → UTC = Mon 07:59:59 UTC


def _jst_to_utc(year, month, day, hour=0, minute=0, second=0):
    """Convert JST datetime to UTC."""
    dt = datetime(year, month, day, hour, minute, second, tzinfo=JST)
    return dt.astimezone(timezone.utc)


def _pst_to_utc(year, month, day, hour=23, minute=59, second=59):
    """Convert PST datetime to UTC."""
    dt = datetime(year, month, day, hour, minute, second, tzinfo=PST)
    return dt.astimezone(timezone.utc)


BLOCK_DEFINITIONS = [
    {
        "block_id": "block_1",
        "label": "Block 1 — Mar 1 (Sunday)",
        "window_open_utc": _jst_to_utc(2026, 3, 1),       # Sun Mar 1 00:00 JST
        "window_close_utc": _pst_to_utc(2026, 3, 1),       # Sun Mar 1 23:59:59 PST
        "sports": ["Swimming"],
    },
    {
        "block_id": "block_2",
        "label": "Block 2 — Mar 6–8",
        "window_open_utc": _jst_to_utc(2026, 3, 6),        # Fri Mar 6 00:00 JST
        "window_close_utc": _pst_to_utc(2026, 3, 8),       # Sun Mar 8 23:59:59 PST
        "sports": ["Cycling", "Running", "Swimming"],
    },
    {
        "block_id": "block_3",
        "label": "Block 3 — Mar 13–15",
        "window_open_utc": _jst_to_utc(2026, 3, 13),
        "window_close_utc": _pst_to_utc(2026, 3, 15),
        "sports": ["Cycling", "Running", "Swimming"],
    },
    {
        "block_id": "block_4",
        "label": "Block 4 — Mar 20–22",
        "window_open_utc": _jst_to_utc(2026, 3, 20),
        "window_close_utc": _pst_to_utc(2026, 3, 22),
        "sports": ["Cycling", "Running", "Swimming"],
    },
    {
        "block_id": "block_5",
        "label": "Block 5 — Mar 27–29",
        "window_open_utc": _jst_to_utc(2026, 3, 27),
        "window_close_utc": _pst_to_utc(2026, 3, 29),
        "sports": ["Cycling", "Running", "Swimming"],
    },
]


def get_block_for_activity(start_date_utc: datetime) -> str | None:
    """Return block_id if the activity falls within a block window, else None."""
    for block in BLOCK_DEFINITIONS:
        if block["window_open_utc"] <= start_date_utc <= block["window_close_utc"]:
            return block["block_id"]
    return None


def get_sport_category(sport_type: str) -> str | None:
    """Map Strava sport_type to our sport category, or None if not valid."""
    return VALID_SPORT_TYPES.get(sport_type)
