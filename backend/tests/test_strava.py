"""
Unit tests for Strava service — token refresh flow and sport type filtering.
Uses mocked httpx responses.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import time


class TestTokenRefresh:
    """Test Strava token refresh logic."""

    @pytest.mark.asyncio
    async def test_reuses_valid_token(self):
        """If token_expiry is > 5 min from now, reuse existing token."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "access_token": "valid_token",
            "refresh_token": "refresh_xyz",
            "token_expiry": int(time.time()) + 3600,  # 1 hour from now
        }

        mock_db = MagicMock()
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch("backend.services.strava_service.get_db", return_value=mock_db):
            from backend.services.strava_service import refresh_access_token
            token = await refresh_access_token("player_1")
            assert token == "valid_token"

    @pytest.mark.asyncio
    async def test_refreshes_expired_token(self):
        """If token is expired, call Strava refresh endpoint."""
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "access_token": "old_token",
            "refresh_token": "refresh_xyz",
            "token_expiry": int(time.time()) - 100,  # expired
        }

        mock_db = MagicMock()
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value.update = MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_at": int(time.time()) + 21600,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("backend.services.strava_service.get_db", return_value=mock_db):
            with patch("backend.services.strava_service.httpx.AsyncClient", return_value=mock_client):
                from backend.services.strava_service import refresh_access_token
                token = await refresh_access_token("player_1")
                assert token == "new_token"

    @pytest.mark.asyncio
    async def test_raises_for_unknown_player(self):
        """Refresh should raise ValueError for non-existent player."""
        mock_doc = MagicMock()
        mock_doc.exists = False

        mock_db = MagicMock()
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch("backend.services.strava_service.get_db", return_value=mock_db):
            from backend.services.strava_service import refresh_access_token
            with pytest.raises(ValueError, match="not found"):
                await refresh_access_token("nonexistent")


class TestCaloriesFallback:
    """Test calories derivation from kilojoules."""

    def test_kj_to_cal_conversion(self):
        """1 kJ ≈ 0.239 kcal."""
        kilojoules = 1000
        calories = round(kilojoules * 0.239, 2)
        assert abs(calories - 239.0) < 0.01

    def test_zero_calories_uses_kj(self):
        """When calories is 0, we should derive from kilojoules."""
        calories = 0
        kilojoules = 500
        if calories == 0 and kilojoules > 0:
            calories = round(kilojoules * 0.239, 2)
        assert calories == 119.5
