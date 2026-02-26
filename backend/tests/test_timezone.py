"""
Unit tests for timezone/window calculations.
Tests: block window UTC conversions, activity inside/outside windows,
JST open and PST close edge cases.
"""
import pytest
from datetime import datetime, timezone, timedelta
from backend.config import (
    BLOCK_DEFINITIONS,
    get_block_for_activity,
    get_sport_category,
    JST,
    PST,
)


class TestBlockWindows:
    """Verify block windows are correctly calculated in UTC."""

    def test_block1_opens_sunday_00_jst(self):
        """Block 1 opens Sun Mar 1 00:00 JST = Sat Feb 28 15:00 UTC."""
        block1 = BLOCK_DEFINITIONS[0]
        expected_open = datetime(2026, 2, 28, 15, 0, 0, tzinfo=timezone.utc)
        assert block1["window_open_utc"] == expected_open

    def test_block1_closes_sunday_2359_pst(self):
        """Block 1 closes Sun Mar 1 23:59:59 PST = Mon Mar 2 07:59:59 UTC."""
        block1 = BLOCK_DEFINITIONS[0]
        expected_close = datetime(2026, 3, 2, 7, 59, 59, tzinfo=timezone.utc)
        assert block1["window_close_utc"] == expected_close

    def test_block2_opens_friday_00_jst(self):
        """Block 2 opens Fri Mar 6 00:00 JST = Thu Mar 5 15:00 UTC."""
        block2 = BLOCK_DEFINITIONS[1]
        expected_open = datetime(2026, 3, 5, 15, 0, 0, tzinfo=timezone.utc)
        assert block2["window_open_utc"] == expected_open

    def test_block2_closes_sunday_2359_pst(self):
        """Block 2 closes Sun Mar 8 23:59:59 PST = Mon Mar 9 07:59:59 UTC."""
        block2 = BLOCK_DEFINITIONS[1]
        expected_close = datetime(2026, 3, 9, 7, 59, 59, tzinfo=timezone.utc)
        assert block2["window_close_utc"] == expected_close

    def test_block5_window(self):
        """Block 5: Fri Mar 27 00:00 JST → Sun Mar 29 23:59:59 PST."""
        block5 = BLOCK_DEFINITIONS[4]
        assert block5["window_open_utc"] == datetime(2026, 3, 26, 15, 0, 0, tzinfo=timezone.utc)
        assert block5["window_close_utc"] == datetime(2026, 3, 30, 7, 59, 59, tzinfo=timezone.utc)


class TestActivityBlockAssignment:
    """Test get_block_for_activity()."""

    def test_activity_inside_block1(self):
        """Activity on Mar 1 06:00 UTC → inside Block 1."""
        dt = datetime(2026, 3, 1, 6, 0, 0, tzinfo=timezone.utc)
        assert get_block_for_activity(dt) == "block_1"

    def test_activity_outside_all_blocks(self):
        """Activity on Mar 3 → between blocks, not in any."""
        dt = datetime(2026, 3, 3, 12, 0, 0, tzinfo=timezone.utc)
        assert get_block_for_activity(dt) is None

    def test_activity_at_block_open_boundary(self):
        """Activity exactly at block open time → included."""
        block2 = BLOCK_DEFINITIONS[1]
        dt = block2["window_open_utc"]
        assert get_block_for_activity(dt) == "block_2"

    def test_activity_at_block_close_boundary(self):
        """Activity exactly at block close time → included."""
        block2 = BLOCK_DEFINITIONS[1]
        dt = block2["window_close_utc"]
        assert get_block_for_activity(dt) == "block_2"

    def test_activity_just_after_block_close(self):
        """Activity 1 second after block close → not included."""
        block2 = BLOCK_DEFINITIONS[1]
        dt = block2["window_close_utc"] + timedelta(seconds=1)
        assert get_block_for_activity(dt) is None

    def test_activity_before_block1_open(self):
        """Activity before first block opens → no block."""
        dt = datetime(2026, 2, 28, 14, 0, 0, tzinfo=timezone.utc)
        assert get_block_for_activity(dt) is None


class TestSportCategoryMapping:
    """Test get_sport_category()."""

    def test_valid_cycling_types(self):
        assert get_sport_category("Ride") == "Cycling"
        assert get_sport_category("MountainBikeRide") == "Cycling"
        assert get_sport_category("GravelRide") == "Cycling"

    def test_valid_running_types(self):
        assert get_sport_category("Run") == "Running"
        assert get_sport_category("TrailRun") == "Running"

    def test_valid_swimming(self):
        assert get_sport_category("Swim") == "Swimming"

    def test_invalid_types_return_none(self):
        assert get_sport_category("Hike") is None
        assert get_sport_category("Yoga") is None
        assert get_sport_category("Walk") is None
        assert get_sport_category("VirtualRide") is None
        assert get_sport_category("EBikeRide") is None
        assert get_sport_category("WeightTraining") is None
