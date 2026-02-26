"""
Scoring service — calculates and locks block scores.

Scoring rules:
- Per sport: sum calories per player. Higher = 2pts, lower = 0pts, tie = 1pt each.
  Solo (only one player logged) = 2pts. Neither logged = 0pts.
- Clean sweep: if BOTH players logged ALL sports for the block AND one player won
  ALL sports → winner gets +1 bonus.
- Block 1 special: Swimming only. Winner gets 2 + 1 bonus = 3 max.
"""
from datetime import datetime, timezone
from collections import defaultdict
from config import BLOCK_DEFINITIONS
from firebase_client import get_db


def _get_block_def(block_id: str) -> dict | None:
    for b in BLOCK_DEFINITIONS:
        return next((b for b in BLOCK_DEFINITIONS if b["block_id"] == block_id), None)


def calculate_block_scores(block_id: str) -> dict:
    """
    Calculate and write scores for a given block.
    Returns the score document. Raises if block is already locked.
    """
    db = get_db()

    # Check lock
    block_doc = db.collection("blocks").document(block_id).get()
    if block_doc.exists and block_doc.to_dict().get("locked", False):
        raise ValueError(f"Block {block_id} is already locked — scores are immutable")

    block_def = next(
        (b for b in BLOCK_DEFINITIONS if b["block_id"] == block_id), None
    )
    if block_def is None:
        raise ValueError(f"Unknown block: {block_id}")

    block_sports = block_def["sports"]  # e.g. ["Swimming"] or all three
    is_block_1 = block_id == "block_1"

    # Get all players
    players = []
    for pdoc in db.collection("athletes").stream():
        pdata = pdoc.to_dict()
        if pdata.get("status") == "connected":
            players.append({"id": pdoc.id, **pdata})

    player_ids = [p["id"] for p in players]

    # Query activities for this block
    activities_ref = db.collection("activities")
    block_activities = list(
        activities_ref.where("block_id", "==", block_id).stream()
    )

    # Group: {player_id: {sport_category: total_calories}}
    calories_by_player_sport = defaultdict(lambda: defaultdict(float))
    # Also track details for dashboard: distance, time
    details_by_player_sport = defaultdict(
        lambda: defaultdict(lambda: {"calories": 0, "distance": 0, "time": 0, "count": 0})
    )

    for adoc in block_activities:
        a = adoc.to_dict()
        pid = a["player_id"]
        sport = a["sport_category"]
        cals = a.get("calories", 0) or 0
        calories_by_player_sport[pid][sport] += cals
        details_by_player_sport[pid][sport]["calories"] += cals
        details_by_player_sport[pid][sport]["distance"] += a.get("distance_meters", 0) or 0
        details_by_player_sport[pid][sport]["time"] += a.get("moving_time_seconds", 0) or 0
        details_by_player_sport[pid][sport]["count"] += 1

    # Score each sport
    calories_by_sport = {}  # {sport: {player_id: total}}
    points_by_sport = {}    # {sport: {player_id: pts}}

    for sport in block_sports:
        sport_calories = {}
        for pid in player_ids:
            sport_calories[pid] = calories_by_player_sport[pid][sport]
        calories_by_sport[sport] = sport_calories

        # Determine who logged
        logged_players = [pid for pid in player_ids if sport_calories[pid] > 0]

        sport_points = {pid: 0 for pid in player_ids}

        if len(logged_players) == 0:
            # Neither logged — 0 points each
            pass
        elif len(logged_players) == 1:
            # Solo — 2 points to the one who logged
            sport_points[logged_players[0]] = 2
        else:
            # Compare all players who logged
            max_cal = max(sport_calories[pid] for pid in logged_players)
            winners = [pid for pid in logged_players if sport_calories[pid] == max_cal]

            if len(winners) == len(logged_players):
                # Everyone tied
                for pid in logged_players:
                    sport_points[pid] = 1
            else:
                # Clear winner(s) get 2, losers get 0
                for pid in winners:
                    sport_points[pid] = 2
                # Losers already 0

        points_by_sport[sport] = sport_points

    # Clean sweep eligibility
    clean_sweep_eligible = {}
    for pid in player_ids:
        # Player logged all sports in this block
        player_logged_all = all(
            calories_by_player_sport[pid][sport] > 0 for sport in block_sports
        )
        clean_sweep_eligible[pid] = player_logged_all

    # Both players must have logged all sports for clean sweep to be possible
    all_eligible = all(clean_sweep_eligible[pid] for pid in player_ids) and len(player_ids) >= 2

    # Check if one player won ALL sports
    clean_sweep_achieved = False
    clean_sweep_winner = None
    bonus_points = {pid: 0 for pid in player_ids}

    if all_eligible:
        for pid in player_ids:
            won_all = all(
                points_by_sport[sport][pid] == 2 for sport in block_sports
            )
            if won_all:
                clean_sweep_achieved = True
                clean_sweep_winner = pid
                bonus_points[pid] = 1
                break
    elif is_block_1:
        # Block 1 special: winning swimming = automatic bonus
        # (only one sport, so "winning all" = winning swimming)
        for pid in player_ids:
            if points_by_sport.get("Swimming", {}).get(pid, 0) == 2:
                clean_sweep_achieved = True
                clean_sweep_winner = pid
                bonus_points[pid] = 1
                break

    # Total points per player
    total_points = {}
    for pid in player_ids:
        total = sum(points_by_sport[sport].get(pid, 0) for sport in block_sports)
        total += bonus_points.get(pid, 0)
        total_points[pid] = total

    # Build score document
    now_utc = datetime.now(timezone.utc).isoformat()
    score_doc = {
        "block_id": block_id,
        "calories_by_sport": calories_by_sport,
        "points_by_sport": points_by_sport,
        "clean_sweep_eligible": clean_sweep_eligible,
        "clean_sweep_achieved": clean_sweep_achieved,
        "clean_sweep_winner": clean_sweep_winner,
        "bonus_points": bonus_points,
        "total_points": total_points,
        "details_by_player_sport": {
            pid: dict(sports) for pid, sports in details_by_player_sport.items()
        },
        "calculated_at": now_utc,
        "locked": True,
    }

    # Write scores
    db.collection("scores").document(block_id).set(score_doc)

    # Lock the block
    db.collection("blocks").document(block_id).update(
        {"locked": True, "calculated_at": now_utc}
    )

    return score_doc


def get_all_scores() -> list[dict]:
    """Retrieve all scored blocks."""
    db = get_db()
    scores = []
    for doc in db.collection("scores").stream():
        scores.append(doc.to_dict())
    return scores


def get_dashboard_data() -> dict:
    """
    Aggregate all data for the frontend dashboard:
    - scoreboard (totals, leader, margin)
    - block grid (per-block scores)
    - sport breakdown (cumulative per sport)
    - projection (if ≥2 blocks locked)
    """
    db = get_db()

    # All players
    players = []
    for pdoc in db.collection("athletes").stream():
        pdata = pdoc.to_dict()
        players.append({"id": pdoc.id, **pdata})

    player_ids = [p["id"] for p in players]

    # All scores
    all_scores = get_all_scores()
    all_scores.sort(key=lambda s: s.get("block_id", ""))

    # Scoreboard — total points
    grand_total = {pid: 0 for pid in player_ids}
    sport_cumulative_calories = {
        pid: {"Cycling": 0, "Running": 0, "Swimming": 0} for pid in player_ids
    }
    sport_cumulative_points = {
        pid: {"Cycling": 0, "Running": 0, "Swimming": 0} for pid in player_ids
    }

    locked_count = 0
    total_bonus_rate = 0

    for score in all_scores:
        if not score.get("locked"):
            continue
        locked_count += 1

        tp = score.get("total_points", {})
        for pid in player_ids:
            grand_total[pid] += tp.get(pid, 0)

        # Sport breakdowns
        cbs = score.get("calories_by_sport", {})
        pbs = score.get("points_by_sport", {})
        for sport in ["Cycling", "Running", "Swimming"]:
            if sport in cbs:
                for pid in player_ids:
                    sport_cumulative_calories[pid][sport] += cbs[sport].get(pid, 0)
            if sport in pbs:
                for pid in player_ids:
                    sport_cumulative_points[pid][sport] += pbs[sport].get(pid, 0)

        # Bonus tracking
        bp = score.get("bonus_points", {})
        total_bonus_rate += sum(bp.values())

    # Leader
    sorted_players = sorted(player_ids, key=lambda pid: grand_total[pid], reverse=True)
    leader = sorted_players[0] if sorted_players else None
    margin = 0
    is_tied = False
    if len(sorted_players) >= 2:
        margin = grand_total[sorted_players[0]] - grand_total[sorted_players[1]]
        is_tied = margin == 0

    # Projection (if ≥2 blocks locked)
    projection = None
    if locked_count >= 2:
        remaining = 5 - locked_count
        avg_bonus_per_block = total_bonus_rate / locked_count if locked_count > 0 else 0
        projected = {}
        for pid in player_ids:
            avg_pts = grand_total[pid] / locked_count
            projected[pid] = round(grand_total[pid] + avg_pts * remaining, 1)
        projection = {
            "projected_totals": projected,
            "remaining_blocks": remaining,
            "avg_bonus_rate": round(avg_bonus_per_block, 2),
        }

        # Determine projected winner
        proj_sorted = sorted(player_ids, key=lambda pid: projected[pid], reverse=True)
        proj_margin = projected[proj_sorted[0]] - projected[proj_sorted[1]] if len(proj_sorted) >= 2 else 0
        projection["projected_winner"] = proj_sorted[0] if proj_margin > 0 else None
        projection["projected_margin"] = round(proj_margin, 1)

        # Can a clean sweep change outcome?
        # If trailing player sweeps all remaining blocks (7 pts each)
        if len(proj_sorted) >= 2:
            trailer = proj_sorted[-1]
            max_catch_up = remaining * 7  # max possible per block
            can_flip = grand_total[trailer] + max_catch_up > grand_total[proj_sorted[0]]
            projection["clean_sweep_can_change_outcome"] = can_flip

    # Get blocks info
    blocks = []
    for bdoc in db.collection("blocks").stream():
        blocks.append(bdoc.to_dict())
    blocks.sort(key=lambda b: b.get("block_id", ""))

    return {
        "players": [
            {
                "id": p["id"],
                "display_name": p.get("display_name"),
                "profile_photo": p.get("profile_photo"),
                "status": p.get("status"),
            }
            for p in players
        ],
        "scoreboard": {
            "totals": grand_total,
            "leader": leader,
            "margin": margin,
            "is_tied": is_tied,
        },
        "block_scores": all_scores,
        "blocks": blocks,
        "sport_breakdown": {
            "cumulative_calories": sport_cumulative_calories,
            "cumulative_points": sport_cumulative_points,
        },
        "projection": projection,
    }
