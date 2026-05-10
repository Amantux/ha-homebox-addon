"""Tests for the Homebox conversation agent."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.homebox.conversation import (
    HomeboxConversationEntity,
    _extract_query,
    _format_item,
)


# ---------------------------------------------------------------------------
# _extract_query
# ---------------------------------------------------------------------------
class TestExtractQuery:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Where is my hammer?", "hammer"),
            ("where's the drill", "drill"),
            ("Where is the socket wrench?", "socket wrench"),
            ("find my passport", "passport"),
            ("locate the extension cord", "extension cord"),
            ("look up the camping tent", "camping tent"),
            ("can you look up my soldering iron?", "soldering iron"),
        ],
    )
    def test_recognizes_patterns(self, text, expected):
        assert _extract_query(text) == expected

    def test_returns_none_for_unknown_pattern(self):
        assert _extract_query("what is 2+2") is None


# ---------------------------------------------------------------------------
# _format_item
# ---------------------------------------------------------------------------
class TestFormatItem:
    def test_with_location(self):
        item = {"name": "Hammer", "location": {"name": "Garage"}, "description": ""}
        result = _format_item(item)
        assert "Hammer" in result
        assert "Garage" in result

    def test_without_location(self):
        item = {"name": "Screwdriver", "location": None, "description": ""}
        result = _format_item(item)
        assert "no location recorded" in result

    def test_with_description(self):
        item = {
            "name": "Drill",
            "location": {"name": "Shed"},
            "description": "18V cordless",
        }
        result = _format_item(item)
        assert "18V cordless" in result


# ---------------------------------------------------------------------------
# HomeboxConversationEntity.async_process
# ---------------------------------------------------------------------------
def _make_entity(items=None, raise_exc=None):
    """Build a HomeboxConversationEntity with a mocked API."""
    from custom_components.homebox.api import CannotConnectError, HomeboxAPI

    api = MagicMock(spec=HomeboxAPI)
    if raise_exc:
        api.async_search_items = AsyncMock(side_effect=raise_exc)
    else:
        api.async_search_items = AsyncMock(return_value=items or [])

    entry = MagicMock()
    entry.entry_id = "test-entry"
    return HomeboxConversationEntity(entry, api)


def _make_input(text: str):
    from unittest.mock import MagicMock

    ui = MagicMock()
    ui.text = text
    ui.language = "en"
    ui.conversation_id = "conv-1"
    return ui


class TestAsyncProcess:
    async def test_found_single_item(self):
        items = [{"name": "Hammer", "location": {"name": "Garage"}, "description": ""}]
        entity = _make_entity(items)
        result = await entity.async_process(_make_input("where is my hammer?"))
        speech = result.response.speech["plain"]["speech"]
        assert "Hammer" in speech
        assert "Garage" in speech

    async def test_found_multiple_items(self):
        items = [
            {"name": "Hammer", "location": {"name": "Garage"}, "description": ""},
            {"name": "Hammer drill", "location": {"name": "Shed"}, "description": ""},
        ]
        entity = _make_entity(items)
        result = await entity.async_process(_make_input("find hammer"))
        speech = result.response.speech["plain"]["speech"]
        assert "2 item" in speech

    async def test_no_items_found(self):
        entity = _make_entity([])
        result = await entity.async_process(_make_input("where is my unicorn?"))
        speech = result.response.speech["plain"]["speech"]
        assert "couldn't find" in speech.lower()

    async def test_connection_error(self):
        from custom_components.homebox.api import CannotConnectError

        entity = _make_entity(raise_exc=CannotConnectError())
        result = await entity.async_process(_make_input("where is my hammer?"))
        speech = result.response.speech["plain"]["speech"]
        assert "couldn't reach" in speech.lower()

    async def test_unknown_pattern_falls_back_to_full_text(self):
        items = [{"name": "Passport", "location": {"name": "Safe"}, "description": ""}]
        entity = _make_entity(items)
        result = await entity.async_process(_make_input("passport"))
        entity._api.async_search_items.assert_called_once_with("passport")
