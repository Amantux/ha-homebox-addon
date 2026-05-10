"""Homebox conversation agent for Home Assistant."""
from __future__ import annotations

import re
from typing import Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CannotConnectError, HomeboxAPI
from .const import DOMAIN

# --- Item search patterns ("where is my X?") ---
_WHERE_PATTERNS = [
    re.compile(r"where(?:'s| is)(?: my| the)?\s+(.+?)[\?\.]*$", re.IGNORECASE),
    re.compile(r"find(?: my| the)?\s+(.+?)[\?\.]*$", re.IGNORECASE),
    re.compile(r"locate(?: my| the)?\s+(.+?)[\?\.]*$", re.IGNORECASE),
    re.compile(r"(?:can you |please )?look up\s+(.+?)[\?\.]*$", re.IGNORECASE),
    re.compile(r"do you know where\s+(.+?)\s+is[\?\.]*$", re.IGNORECASE),
    re.compile(r"search(?:(?: for)?(?: my| the)?)?\s+(.+?)[\?\.]*$", re.IGNORECASE),
]

# --- Location/room query patterns ("what's in the garage?") ---
_LOCATION_PATTERNS = [
    re.compile(
        r"what(?:'s| is)(?: in| inside)(?: the| my)?\s+(.+?)[\?\.]*$", re.IGNORECASE
    ),
    re.compile(
        r"(?:show|list)(?: me)?(?: everything| all items?)?(?: in| inside)(?: the| my)?\s+(.+?)[\?\.]*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"what(?:'s| is)(?: stored)?(?: in| inside)(?: the| my)?\s+(.+?)[\?\.]*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:items?|stuff|things?)(?: in| inside)(?: the| my)?\s+(.+?)[\?\.]*$",
        re.IGNORECASE,
    ),
]

_LEADING_ARTICLES = re.compile(r"^(?:my|the|a|an)\s+", re.IGNORECASE)
# Short words to skip when building fallback keyword searches
_STOP_WORDS = {"a", "an", "the", "my", "is", "in", "at", "it", "of", "or", "and"}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    api: HomeboxAPI = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([HomeboxConversationEntity(config_entry, api)])


def _extract_item_query(text: str) -> str | None:
    """Return the item search term, or None if this is not an item query."""
    for pattern in _WHERE_PATTERNS:
        match = pattern.search(text.strip())
        if match:
            raw = match.group(1).strip()
            return _LEADING_ARTICLES.sub("", raw).strip()
    return None


def _extract_location_query(text: str) -> str | None:
    """Return the location name, or None if this is not a location query."""
    for pattern in _LOCATION_PATTERNS:
        match = pattern.search(text.strip())
        if match:
            raw = match.group(1).strip()
            return _LEADING_ARTICLES.sub("", raw).strip()
    return None


def _format_item(item: dict) -> str:
    """Format a single Homebox item into a readable sentence."""
    name = item.get("name", "Unknown item")
    location = item.get("location") or {}
    location_name = location.get("name")
    description = (item.get("description") or "").strip()

    parts = [f"**{name}**"]
    if location_name:
        parts.append(f"is in **{location_name}**")
    else:
        parts.append("has no location recorded")
    if description:
        parts.append(f"({description})")
    return " ".join(parts)


def _format_items_response(items: list[dict], query: str) -> str:
    """Build a human-readable response for a list of matching items."""
    if not items:
        return f"I couldn't find anything matching **{query}** in your inventory."
    if len(items) == 1:
        return f"I found one item: {_format_item(items[0])}."
    lines = "\n".join(f"- {_format_item(i)}" for i in items[:10])
    result = f"I found {len(items)} item(s) matching **{query}**:\n{lines}"
    if len(items) > 10:
        result += f"\n...and {len(items) - 10} more."
    return result


def _keyword_fallbacks(query: str) -> list[str]:
    """Break a multi-word query into individual keywords to try separately."""
    words = [w for w in query.lower().split() if w not in _STOP_WORDS and len(w) > 2]
    return list(dict.fromkeys(words))  # deduplicated, order-preserving


class HomeboxConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """Conversation agent that queries Homebox inventory."""

    _attr_has_entity_name = True
    _attr_name = "Homebox"
    _attr_supported_languages = "*"

    def __init__(self, entry: ConfigEntry, api: HomeboxAPI) -> None:
        self._entry = entry
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_conversation"

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        return "*"

    async def _search_items(self, query: str) -> tuple[list[dict], str]:
        """
        Search by query; if no results, try individual keywords as fallback.
        Returns (items, effective_query_used).
        """
        items = await self._api.async_search_items(query)
        if items:
            return items, query

        for keyword in _keyword_fallbacks(query):
            items = await self._api.async_search_items(keyword)
            if items:
                return items, keyword

        return [], query

    async def _handle_location_query(self, location_name: str) -> str:
        """Look up a location by name and list everything stored there."""
        locations = await self._api.async_list_locations()
        match = next(
            (
                loc
                for loc in locations
                if location_name.lower() in loc.get("name", "").lower()
            ),
            None,
        )
        if match is None:
            known = ", ".join(f"**{loc['name']}**" for loc in locations[:10])
            suffix = f"\n\nKnown locations: {known}" if known else ""
            return f"I couldn't find a location matching **{location_name}**.{suffix}"

        items = await self._api.async_get_items_in_location(match["id"])
        loc_display = match["name"]
        if not items:
            return f"**{loc_display}** exists but has no items recorded in it."
        lines = "\n".join(f"- **{i.get('name', '?')}**" for i in items[:20])
        result = f"**{loc_display}** contains {len(items)} item(s):\n{lines}"
        if len(items) > 20:
            result += f"\n...and {len(items) - 20} more."
        return result

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a natural-language inventory query."""
        text = user_input.text

        try:
            location_query = _extract_location_query(text)
            if location_query:
                response_text = await self._handle_location_query(location_query)
            else:
                item_query = _extract_item_query(text) or text.strip()
                items, effective_query = await self._search_items(item_query)
                response_text = _format_items_response(items, effective_query)

        except CannotConnectError:
            response_text = (
                "I couldn't reach Homebox right now. "
                "Please check that the add-on is running."
            )

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)
        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id,
        )
