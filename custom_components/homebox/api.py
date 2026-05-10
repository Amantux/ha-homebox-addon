"""Homebox API client."""
from __future__ import annotations

from typing import Any

import aiohttp


class CannotConnectError(Exception):
    """Raised when connection to Homebox fails."""


class InvalidAuthError(Exception):
    """Raised when the API token is rejected."""


class HomeboxAPI:
    """Async client for the Homebox REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        token: str,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}

    async def async_verify_auth(self) -> None:
        """Test connectivity and authentication. Raises on failure."""
        try:
            async with self._session.get(
                f"{self._base_url}/api/v1/users/self",
                headers=self._headers,
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuthError
                resp.raise_for_status()
        except aiohttp.ClientError as err:
            raise CannotConnectError from err

    async def async_search_items(self, query: str) -> list[dict[str, Any]]:
        """Search inventory items by keyword. Returns a list of item dicts."""
        try:
            async with self._session.get(
                f"{self._base_url}/api/v1/items",
                headers=self._headers,
                params={"search": query},
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuthError
                resp.raise_for_status()
                data = await resp.json()
                return data.get("items", [])
        except aiohttp.ClientError as err:
            raise CannotConnectError from err

    async def async_get_item(self, item_id: str) -> dict[str, Any]:
        """Fetch a single item by ID (includes full location path)."""
        try:
            async with self._session.get(
                f"{self._base_url}/api/v1/items/{item_id}",
                headers=self._headers,
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuthError
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise CannotConnectError from err
