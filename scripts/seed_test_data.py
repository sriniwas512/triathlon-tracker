"""
Seed test data script — creates mock activity data across all 5 blocks
for two players, covering all scoring scenarios:
- Clean sweep achieved
- Clean sweep eligible but not achieved
- One player missing a sport
- Ties
- Block 1 standalone Sunday (Swimming only)
"""
import sys
import os
import json
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.firebase_client import get_db
from backend.services.block_service import seed_blocks, seed_players
from backend.config import BLOCK_DEFINITIONS

# Player IDs
P1 = "player_1"
P2 = "player_2"


def clear_collections(db):
    """Clear activities and scores collections for fresh seeding."""
    for coll in ["activities", "scores"]:
        docs = db.collection(coll).stream()
        for doc in docs:
            doc.reference.delete()

    # Unlock all blocks
    for doc in db.collection("blocks").stream():
        doc.reference.update({"locked": False, "calculated_at": None})


def add_activity(db, activity_id, player_id, sport_type, sport_category,
                 block_id, start_date_utc, calories, distance_m=5000,
                 moving_time_s=1800, kilojoules=0, name="Test Activity"):
    """Insert a test activity document."""
    db.collection("activities").document(str(activity_id)).set({
        "activity_id": str(activity_id),
        "player_id": player_id,
        "strava_athlete_id": f"strava_{player_id}",
        "sport_type": sport_type,
        "sport_category": sport_category,
        "block_id": block_id,
        "start_date_utc": start_date_utc.isoformat(),
        "calories": calories,
        "kilojoules": kilojoules,
        "distance_meters": distance_m,
        "moving_time_seconds": moving_time_s,
        "name": name,
    })


def seed():
    db = get_db()

    # Ensure blocks and players exist
    seed_blocks()
    seed_players()

    # Mark players as connected (so dashboard works)
    for i, pid in enumerate([P1, P2]):
        db.collection("athletes").document(pid).update({
            "status": "connected",
            "display_name": f"Athlete {chr(65+i)}",  # Athlete A, Athlete B
            "strava_athlete_id": f"strava_{pid}",
            "profile_photo": None,
        })

    # Clear old test data
    clear_collections(db)

    aid = 1000  # activity ID counter

    # ─── Block 1: Mar 1 (Sunday) — Swimming Only ───
    # P1 wins swimming → gets 2 + 1 bonus = 3
    b1_start = datetime(2026, 3, 1, 2, 0, 0, tzinfo=timezone.utc)  # within window
    add_activity(db, aid, P1, "Swim", "Swimming", "block_1", b1_start, 450, 1500, 2700, 0, "Morning Swim")
    aid += 1
    add_activity(db, aid, P2, "Swim", "Swimming", "block_1", b1_start + timedelta(hours=3), 320, 1200, 2400, 0, "Pool Session")
    aid += 1

    # ─── Block 2: Mar 6–8 — Clean Sweep by P1 ───
    # P1 wins all 3 sports, both log all 3 → clean sweep +1 bonus
    b2_start = datetime(2026, 3, 6, 16, 0, 0, tzinfo=timezone.utc)  # Sat morning JST

    # Cycling
    add_activity(db, aid, P1, "Ride", "Cycling", "block_2", b2_start, 800, 40000, 5400, 0, "Long Ride")
    aid += 1
    add_activity(db, aid, P2, "Ride", "Cycling", "block_2", b2_start + timedelta(hours=1), 500, 25000, 3600, 0, "Easy Ride")
    aid += 1

    # Running
    add_activity(db, aid, P1, "Run", "Running", "block_2", b2_start + timedelta(hours=5), 600, 10000, 3000, 0, "10K Run")
    aid += 1
    add_activity(db, aid, P2, "TrailRun", "Running", "block_2", b2_start + timedelta(hours=6), 400, 7000, 2700, 0, "Trail Jog")
    aid += 1

    # Swimming
    add_activity(db, aid, P1, "Swim", "Swimming", "block_2", b2_start + timedelta(days=1), 350, 2000, 2400, 0, "Pool Laps")
    aid += 1
    add_activity(db, aid, P2, "Swim", "Swimming", "block_2", b2_start + timedelta(days=1, hours=2), 280, 1500, 2100, 0, "Open Water Swim")
    aid += 1

    # ─── Block 3: Mar 13–15 — Tie scenario + Player 2 missing Running ───
    # P1 and P2 tie in Cycling, P1 wins Swimming, P2 didn't run
    b3_start = datetime(2026, 3, 13, 16, 0, 0, tzinfo=timezone.utc)

    # Cycling — TIE
    add_activity(db, aid, P1, "GravelRide", "Cycling", "block_3", b3_start, 550, 35000, 4800, 0, "Gravel Adventure")
    aid += 1
    add_activity(db, aid, P2, "MountainBikeRide", "Cycling", "block_3", b3_start + timedelta(hours=2), 550, 30000, 5100, 0, "MTB Trail")
    aid += 1

    # Running — only P1
    add_activity(db, aid, P1, "Run", "Running", "block_3", b3_start + timedelta(hours=8), 500, 8000, 2400, 0, "Evening Run")
    aid += 1
    # P2 didn't run — no activity

    # Swimming — P1 wins
    add_activity(db, aid, P1, "Swim", "Swimming", "block_3", b3_start + timedelta(days=1), 400, 2500, 2700, 0, "Distance Swim")
    aid += 1
    add_activity(db, aid, P2, "Swim", "Swimming", "block_3", b3_start + timedelta(days=1, hours=1), 300, 1800, 2100, 0, "Quick Dip")
    aid += 1

    # ─── Block 4: Mar 20–22 — Clean Sweep Eligible but Not Achieved ───
    # Both log all 3 but neither wins all → no bonus
    b4_start = datetime(2026, 3, 20, 16, 0, 0, tzinfo=timezone.utc)

    # Cycling — P2 wins
    add_activity(db, aid, P1, "Ride", "Cycling", "block_4", b4_start, 600, 38000, 5100, 0, "Training Ride")
    aid += 1
    add_activity(db, aid, P2, "Ride", "Cycling", "block_4", b4_start + timedelta(hours=1), 750, 45000, 5700, 0, "Century Ride")
    aid += 1

    # Running — P1 wins
    add_activity(db, aid, P1, "Run", "Running", "block_4", b4_start + timedelta(hours=6), 650, 12000, 3600, 0, "Half Marathon Prep")
    aid += 1
    add_activity(db, aid, P2, "Run", "Running", "block_4", b4_start + timedelta(hours=7), 480, 8000, 2700, 0, "Recovery Run")
    aid += 1

    # Swimming — P2 wins
    add_activity(db, aid, P1, "Swim", "Swimming", "block_4", b4_start + timedelta(days=1), 250, 1500, 1800, 0, "Easy Swim")
    aid += 1
    add_activity(db, aid, P2, "Swim", "Swimming", "block_4", b4_start + timedelta(days=1, hours=1), 420, 2800, 3000, 0, "Endurance Swim")
    aid += 1

    # ─── Block 5: Mar 27–29 — P2 sweeps ───
    b5_start = datetime(2026, 3, 27, 16, 0, 0, tzinfo=timezone.utc)

    # Cycling — P2 wins
    add_activity(db, aid, P1, "Ride", "Cycling", "block_5", b5_start, 580, 37000, 5000, 0, "Final Ride")
    aid += 1
    add_activity(db, aid, P2, "Ride", "Cycling", "block_5", b5_start + timedelta(hours=1), 900, 55000, 6300, 0, "Race Day Ride")
    aid += 1

    # Running — P2 wins
    add_activity(db, aid, P1, "Run", "Running", "block_5", b5_start + timedelta(hours=5), 450, 7500, 2400, 0, "Light Run")
    aid += 1
    add_activity(db, aid, P2, "TrailRun", "Running", "block_5", b5_start + timedelta(hours=6), 700, 15000, 4200, 0, "Trail Ultra")
    aid += 1

    # Swimming — P2 wins
    add_activity(db, aid, P1, "Swim", "Swimming", "block_5", b5_start + timedelta(days=1), 300, 1800, 2100, 0, "Final Swim")
    aid += 1
    add_activity(db, aid, P2, "Swim", "Swimming", "block_5", b5_start + timedelta(days=1, hours=1), 500, 3000, 3300, 0, "Championship Swim")
    aid += 1

    print("✅ Seeded test data successfully!")
    print(f"   Total activities: {aid - 1000}")
    print()
    print("Expected scoring:")
    print("  Block 1: P1=3 (swim win + bonus), P2=0")
    print("  Block 2: P1=7 (sweep: 6+1), P2=0")
    print("  Block 3: P1=5 (tie cycling 1, solo run 2, win swim 2), P2=1 (tie cycling)")
    print("  Block 4: P1=2, P2=4 (both logged all, split wins, no sweep)")
    print("  Block 5: P1=0, P2=7 (P2 sweeps)")
    print("  TOTAL:   P1=17, P2=12")


if __name__ == "__main__":
    seed()
