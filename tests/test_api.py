"""Tests for the Homebox API client."""
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.homebox.api import (
    CannotConnectError,
    HomeboxAPI,
    InvalidAuthError,
)


def _make_api(status: int, payload: dict | None = None, raise_exc=None):
    """Return an (api, mock_response) pair wired to return the given status/payload."""
    session = MagicMock(spec=aiohttp.ClientSession)
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=payload or {})
    mock_resp.raise_for_status = MagicMock()
    if raise_exc:
        session.get.return_value.__aenter__ = AsyncMock(side_effect=raise_exc)
    else:
        session.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    session.get.return_value.__aexit__ = AsyncMock(return_value=False)
    return HomeboxAPI(session, "http://homebox.local", "test-token"), mock_resp


class TestAsyncVerifyAuth:
    async def test_success(self):
        api, _ = _make_api(200, {"id": "user-1"})
        await api.async_verify_auth()  # should not raise

    async def test_invalid_auth(self):
        api, resp = _make_api(401)
        resp.raise_for_status = MagicMock()
        with pytest.raises(InvalidAuthError):
            await api.async_verify_auth()

    async def test_connection_error(self):
        api, _ = _make_api(0, raise_exc=aiohttp.ClientError("timeout"))
        with pytest.raises(CannotConnectError):
            await api.async_verify_auth()


class TestAsyncSearchItems:
    async def test_returns_items(self):
        payload = {
            "items": [
                {"id": "1", "name": "Hammer", "location": {"name": "Garage"}},
                {"id": "2", "name": "Hammer drill", "location": {"name": "Shed"}},
            ]
        }
        api, _ = _make_api(200, payload)
        items = await api.async_search_items("hammer")
        assert len(items) == 2
        assert items[0]["name"] == "Hammer"

    async def test_empty_results(self):
        api, _ = _make_api(200, {"items": []})
        items = await api.async_search_items("unobtanium")
        assert items == []

    async def test_missing_items_key(self):
        api, _ = _make_api(200, {})
        items = await api.async_search_items("x")
        assert items == []

    async def test_invalid_auth_raises(self):
        api, _ = _make_api(401)
        with pytest.raises(InvalidAuthError):
            await api.async_search_items("x")

    async def test_connection_error_raises(self):
        api, _ = _make_api(0, raise_exc=aiohttp.ClientError("err"))
        with pytest.raises(CannotConnectError):
            await api.async_search_items("x")
