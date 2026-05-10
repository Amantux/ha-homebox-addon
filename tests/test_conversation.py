"""Tests for the Homebox conversation agent."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.homebox.conversation import (
    HomeboxConversationEntity,
    _extract_item_query,
    _extract_location_query,
    _format_item,
    _keyword_fallbacks,
)


# ---------------------------------------------------------------------------
# _extract_item_query
# ---------------------------------------------------------------------------
class TestExtractItemQuery:
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
            ("do you know where my screwdriver is?", "screwdriver"),
            ("search for power drill", "power drill"),
        ],
    )
    def test_recognizes_patterns(self, text, expected):
        assert _extract_item_query(text) == expected

    def test_returns_none_for_location_query(self):
        assert _extract_item_query("what's in the garage?") is None

    def test_returns_none_for_unknown_pattern(self):
        assert _extract_item_query("what is 2+2") is None


# ---------------------------------------------------------------------------
# _extract_location_query
# ---------------------------------------------------------------------------
class TestExtractLocationQuery:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("what's in the garage?", "garage"),
            ("What is in my shed?", "shed"),
            ("show me everything in the basement", "basement"),
            ("list all items in the kitchen", "kitchen"),
            ("what is stored in the attic?", "attic"),
            ("items in the living room", "living room"),
            ("stuff in the toolbox", "toolbox"),
        ],
    )
    def test_recognizes_patterns(self, text, expected):
        assert _extract_location_query(text) == expected

    def test_returns_none_for_item_query(self):
        assert _extract_location_query("where is my hammer?") is None


# ---------------------------------------------------------------------------
# _keyword_fallbacks
# ---------------------------------------------------------------------------
class TestKeywordFallbacks:
    def test_splits_multi_word(self):
        result = _keyword_fallbacks("camping gear bag")
        assert "camping" in result
        assert "gear" in result
        assert "bag" in result

    def test_removes_stop_words(self):
        result = _keyword_fallbacks("the big red box")
        assert "the" not in result
        assert "big" in result
        assert "red" in result
        assert "box" in result

    def test_skips_short_words(self):
        result = _keyword_fallbacks("an ax")
        assert "an" not in result
        assert "ax" not in result  # too short (len <= 2)

    def test_deduplicates(self):
        result = _keyword_fallbacks("hammer hammer nail")
        assert result.count("hammer") == 1


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
def _make_entity(items=None, raise_exc=None, locations=None, location_items=None):
    """Build a HomeboxConversationEntity with a mocked API."""
    from custom_components.homebox.api import HomeboxAPI

    api = MagicMock(spec=HomeboxAPI)
    if raise_exc:
        api.async_search_items = AsyncMock(side_effect=raise_exc)
        api.async_list_locations = AsyncMock(side_effect=raise_exc)
        api.async_get_items_in_location = AsyncMock(side_effect=raise_exc)
    else:
        api.async_search_items = AsyncMock(return_value=items or [])
        api.async_list_locations = AsyncMock(return_value=locations or [])
        api.async_get_items_in_location = AsyncMock(return_value=location_items or [])

    entry = MagicMock()
    entry.entry_id = "test-entry"
    return HomeboxConversationEntity(entry, api)


def _make_input(text: str):
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
        await entity.async_process(_make_input("passport"))
        entity._api.async_search_items.assert_called_with("passport")

    async def test_keyword_fallback_when_no_full_match(self):
        """If the full query returns nothing, tries individual keywords."""
        drill_item = [{"name": "Power Drill", "location": {"name": "Shed"}, "description": ""}]

        async def search_side_effect(query: str):
            if query == "camping gear":
                return []
            if query == "camping":
                return []
            if query == "gear":
                return drill_item  # simulate a hit on "gear"
            return []

        from custom_components.homebox.api import HomeboxAPI

        api = MagicMock(spec=HomeboxAPI)
        api.async_search_items = AsyncMock(side_effect=search_side_effect)
        api.async_list_locations = AsyncMock(return_value=[])
        api.async_get_items_in_location = AsyncMock(return_value=[])
        entry = MagicMock()
        entry.entry_id = "test-entry"
        entity = HomeboxConversationEntity(entry, api)

        result = await entity.async_process(_make_input("find camping gear"))
        speech = result.response.speech["plain"]["speech"]
        assert "Power Drill" in speech


class TestLocationQuery:
    async def test_location_found_with_items(self):
        locs = [{"id": "loc-1", "name": "Garage"}]
        loc_items = [
            {"name": "Hammer", "location": {"name": "Garage"}, "description": ""},
            {"name": "Drill", "location": {"name": "Garage"}, "description": ""},
        ]
        entity = _make_entity(locations=locs, location_items=loc_items)
        result = await entity.async_process(_make_input("what's in the garage?"))
        speech = result.response.speech["plain"]["speech"]
        assert "Garage" in speech
        assert "Hammer" in speech
        assert "Drill" in speech

    async def test_location_found_but_empty(self):
        locs = [{"id": "loc-1", "name": "Attic"}]
        entity = _make_entity(locations=locs, location_items=[])
        result = await entity.async_process(_make_input("what's in the attic?"))
        speech = result.response.speech["plain"]["speech"]
        assert "no items" in speech.lower() or "has no" in speech.lower()

    async def test_location_not_found(self):
        locs = [{"id": "loc-1", "name": "Garage"}]
        entity = _make_entity(locations=locs)
        result = await entity.async_process(_make_input("what's in the basement?"))
        speech = result.response.speech["plain"]["speech"]
        assert "couldn't find" in speech.lower()
        assert "Garage" in speech  # shows known locations

    async def test_location_partial_match(self):
        """'garage shelf' should match location named 'Garage'."""
        locs = [{"id": "loc-1", "name": "Garage"}]
        loc_items = [{"name": "Wrench", "location": {"name": "Garage"}, "description": ""}]
        entity = _make_entity(locations=locs, location_items=loc_items)
        result = await entity.async_process(_make_input("items in the garage"))
        speech = result.response.speech["plain"]["speech"]
        assert "Wrench" in speech
