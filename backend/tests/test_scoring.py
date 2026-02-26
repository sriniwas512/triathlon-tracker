"""
Unit tests for the scoring engine.
Tests cover: base scoring, clean sweep eligibility, clean sweep bonus,
Block 1 edge case, and locked block immutability.
"""
import pytest
from unittest.mock import MagicMock, patch
from collections import defaultdict
from datetime import datetime, timezone


# ─── Helpers to build a mock Firestore ───

class MockDoc:
    def __init__(self, doc_id, data, exists=True):
        self.id = doc_id
        self._data = data
        self.exists = exists
        self.reference = MagicMock()

    def to_dict(self):
        return self._data


class MockCollection:
    def __init__(self, docs=None):
        self._docs = {d.id: d for d in (docs or [])}

    def document(self, doc_id):
        ref = MagicMock()
        doc = self._docs.get(doc_id, MockDoc(doc_id, {}, exists=False))
        ref.get.return_value = doc
        ref.set = MagicMock()
        ref.update = MagicMock()
        return ref

    def where(self, field, op, value):
        results = [d for d in self._docs.values() if d._data.get(field) == value]
        mock = MagicMock()
        mock.stream.return_value = results
        return mock

    def stream(self):
        return list(self._docs.values())


class MockDB:
    def __init__(self, collections):
        self._colls = collections

    def collection(self, name):
        return self._colls.get(name, MockCollection())


# ─── Test fixtures ───

def make_player(pid, name):
    return MockDoc(pid, {
        "display_name": name,
        "status": "connected",
        "strava_athlete_id": f"strava_{pid}",
    })


def make_activity(aid, pid, sport_type, sport_cat, block_id, calories,
                  distance=5000, time_s=1800):
    return MockDoc(str(aid), {
        "activity_id": str(aid),
        "player_id": pid,
        "sport_type": sport_type,
        "sport_category": sport_cat,
        "block_id": block_id,
        "calories": calories,
        "distance_meters": distance,
        "moving_time_seconds": time_s,
        "start_date_utc": "2026-03-07T10:00:00+00:00",
    })


def make_block(block_id, locked=False):
    return MockDoc(block_id, {
        "block_id": block_id,
        "locked": locked,
        "calculated_at": None,
    })


# ─── Tests ───

class TestBaseScoring:
    """Test basic point-award logic."""

    def _run_scoring(self, activities, block_id="block_2"):
        """Helper to run calculate_block_scores with mock Firestore."""
        players = [make_player("p1", "Alpha"), make_player("p2", "Beta")]
        blocks = [make_block(block_id, locked=False)]

        db = MockDB({
            "athletes": MockCollection(players),
            "blocks": MockCollection(blocks),
            "activities": MockCollection(activities),
            "scores": MockCollection(),
        })

        with patch("backend.services.scoring_service.get_db", return_value=db):
            from services.scoring_service import calculate_block_scores
            return calculate_block_scores(block_id)

    def test_higher_calories_wins(self):
        """Player with more calories gets 2 points."""
        activities = [
            make_activity(1, "p1", "Ride", "Cycling", "block_2", 800),
            make_activity(2, "p2", "Ride", "Cycling", "block_2", 500),
            make_activity(3, "p1", "Run", "Running", "block_2", 600),
            make_activity(4, "p2", "Run", "Running", "block_2", 400),
            make_activity(5, "p1", "Swim", "Swimming", "block_2", 350),
            make_activity(6, "p2", "Swim", "Swimming", "block_2", 280),
        ]
        result = self._run_scoring(activities)

        assert result["points_by_sport"]["Cycling"]["p1"] == 2
        assert result["points_by_sport"]["Cycling"]["p2"] == 0
        assert result["points_by_sport"]["Running"]["p1"] == 2
        assert result["points_by_sport"]["Running"]["p2"] == 0

    def test_tie_gives_1_each(self):
        """Tied calories should give 1 point each."""
        activities = [
            make_activity(1, "p1", "Ride", "Cycling", "block_2", 500),
            make_activity(2, "p2", "Ride", "Cycling", "block_2", 500),
            make_activity(3, "p1", "Run", "Running", "block_2", 400),
            make_activity(4, "p2", "Run", "Running", "block_2", 400),
            make_activity(5, "p1", "Swim", "Swimming", "block_2", 300),
            make_activity(6, "p2", "Swim", "Swimming", "block_2", 300),
        ]
        result = self._run_scoring(activities)

        assert result["points_by_sport"]["Cycling"]["p1"] == 1
        assert result["points_by_sport"]["Cycling"]["p2"] == 1

    def test_solo_activity_gives_2(self):
        """Only one player logging a sport gets 2 points."""
        activities = [
            make_activity(1, "p1", "Run", "Running", "block_2", 500),
            # P2 didn't log Running
            make_activity(2, "p1", "Ride", "Cycling", "block_2", 600),
            make_activity(3, "p2", "Ride", "Cycling", "block_2", 600),
            make_activity(4, "p1", "Swim", "Swimming", "block_2", 300),
            make_activity(5, "p2", "Swim", "Swimming", "block_2", 300),
        ]
        result = self._run_scoring(activities)

        assert result["points_by_sport"]["Running"]["p1"] == 2
        assert result["points_by_sport"]["Running"]["p2"] == 0

    def test_neither_logged_gives_0(self):
        """No activities for a sport → 0 points each."""
        activities = [
            make_activity(1, "p1", "Ride", "Cycling", "block_2", 600),
            make_activity(2, "p2", "Ride", "Cycling", "block_2", 500),
            # No Running or Swimming
        ]
        result = self._run_scoring(activities)

        assert result["points_by_sport"]["Running"]["p1"] == 0
        assert result["points_by_sport"]["Running"]["p2"] == 0
        assert result["points_by_sport"]["Swimming"]["p1"] == 0
        assert result["points_by_sport"]["Swimming"]["p2"] == 0


class TestCleanSweep:
    """Test clean sweep eligibility and bonus."""

    def _run_scoring(self, activities, block_id="block_2"):
        players = [make_player("p1", "Alpha"), make_player("p2", "Beta")]
        blocks = [make_block(block_id, locked=False)]
        db = MockDB({
            "athletes": MockCollection(players),
            "blocks": MockCollection(blocks),
            "activities": MockCollection(activities),
            "scores": MockCollection(),
        })
        with patch("backend.services.scoring_service.get_db", return_value=db):
            from services.scoring_service import calculate_block_scores
            return calculate_block_scores(block_id)

    def test_clean_sweep_achieved(self):
        """Player wins all 3 sports + both logged all 3 → +1 bonus."""
        activities = [
            make_activity(1, "p1", "Ride", "Cycling", "block_2", 800),
            make_activity(2, "p2", "Ride", "Cycling", "block_2", 500),
            make_activity(3, "p1", "Run", "Running", "block_2", 600),
            make_activity(4, "p2", "Run", "Running", "block_2", 400),
            make_activity(5, "p1", "Swim", "Swimming", "block_2", 350),
            make_activity(6, "p2", "Swim", "Swimming", "block_2", 280),
        ]
        result = self._run_scoring(activities)

        assert result["clean_sweep_achieved"] is True
        assert result["clean_sweep_winner"] == "p1"
        assert result["bonus_points"]["p1"] == 1
        assert result["total_points"]["p1"] == 7  # 6 + 1

    def test_no_sweep_when_player_misses_sport(self):
        """If one player didn't log all 3, no clean sweep possible."""
        activities = [
            make_activity(1, "p1", "Ride", "Cycling", "block_2", 800),
            make_activity(2, "p2", "Ride", "Cycling", "block_2", 500),
            make_activity(3, "p1", "Run", "Running", "block_2", 600),
            # P2 didn't run
            make_activity(5, "p1", "Swim", "Swimming", "block_2", 350),
            make_activity(6, "p2", "Swim", "Swimming", "block_2", 280),
        ]
        result = self._run_scoring(activities)

        assert result["clean_sweep_eligible"]["p1"] is True
        assert result["clean_sweep_eligible"]["p2"] is False
        assert result["clean_sweep_achieved"] is False
        assert result["bonus_points"]["p1"] == 0

    def test_eligible_but_not_achieved(self):
        """Both logged all 3 but wins are split → no bonus."""
        activities = [
            make_activity(1, "p1", "Ride", "Cycling", "block_2", 800),
            make_activity(2, "p2", "Ride", "Cycling", "block_2", 500),
            make_activity(3, "p1", "Run", "Running", "block_2", 400),
            make_activity(4, "p2", "Run", "Running", "block_2", 600),
            make_activity(5, "p1", "Swim", "Swimming", "block_2", 350),
            make_activity(6, "p2", "Swim", "Swimming", "block_2", 280),
        ]
        result = self._run_scoring(activities)

        assert result["clean_sweep_eligible"]["p1"] is True
        assert result["clean_sweep_eligible"]["p2"] is True
        assert result["clean_sweep_achieved"] is False


class TestBlock1EdgeCase:
    """Test Block 1: Swimming only, winner gets 2 + 1 bonus = 3."""

    def _run_scoring(self, activities):
        players = [make_player("p1", "Alpha"), make_player("p2", "Beta")]
        blocks = [make_block("block_1", locked=False)]
        db = MockDB({
            "athletes": MockCollection(players),
            "blocks": MockCollection(blocks),
            "activities": MockCollection(activities),
            "scores": MockCollection(),
        })
        with patch("backend.services.scoring_service.get_db", return_value=db):
            from services.scoring_service import calculate_block_scores
            return calculate_block_scores("block_1")

    def test_block1_swim_winner_gets_3(self):
        """Block 1: swimming winner gets 2 base + 1 bonus = 3."""
        activities = [
            make_activity(1, "p1", "Swim", "Swimming", "block_1", 450),
            make_activity(2, "p2", "Swim", "Swimming", "block_1", 320),
        ]
        result = self._run_scoring(activities)

        assert result["points_by_sport"]["Swimming"]["p1"] == 2
        assert result["points_by_sport"]["Swimming"]["p2"] == 0
        assert result["bonus_points"]["p1"] == 1
        assert result["total_points"]["p1"] == 3
        assert result["total_points"]["p2"] == 0

    def test_block1_only_swimming_scored(self):
        """Block 1 should only have Swimming in points_by_sport."""
        activities = [
            make_activity(1, "p1", "Swim", "Swimming", "block_1", 450),
            make_activity(2, "p2", "Swim", "Swimming", "block_1", 320),
        ]
        result = self._run_scoring(activities)
        assert "Swimming" in result["points_by_sport"]
        assert "Cycling" not in result["points_by_sport"]
        assert "Running" not in result["points_by_sport"]


class TestLockedBlockImmutability:
    """Test that locked blocks cannot be re-scored."""

    def test_locked_block_raises(self):
        players = [make_player("p1", "Alpha"), make_player("p2", "Beta")]
        blocks = [make_block("block_2", locked=True)]
        db = MockDB({
            "athletes": MockCollection(players),
            "blocks": MockCollection(blocks),
            "activities": MockCollection(),
            "scores": MockCollection(),
        })
        with patch("backend.services.scoring_service.get_db", return_value=db):
            from services.scoring_service import calculate_block_scores
            with pytest.raises(ValueError, match="already locked"):
                calculate_block_scores("block_2")
