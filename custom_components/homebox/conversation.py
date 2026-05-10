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

# Patterns that signal a "where is …" query.
# Each captures the raw item phrase; _strip_articles() cleans it up.
_WHERE_PATTERNS = [
    re.compile(r"where(?:'s| is)(?: my| the)?\s+(.+?)[\?\.]*$", re.IGNORECASE),
    re.compile(r"find(?: my| the)?\s+(.+?)[\?\.]*$", re.IGNORECASE),
    re.compile(r"locate(?: my| the)?\s+(.+?)[\?\.]*$", re.IGNORECASE),
    re.compile(r"(?:can you |please )?look up\s+(.+?)[\?\.]*$", re.IGNORECASE),
]

_LEADING_ARTICLES = re.compile(r"^(?:my|the|a|an)\s+", re.IGNORECASE)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    api: HomeboxAPI = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([HomeboxConversationEntity(config_entry, api)])


def _extract_query(text: str) -> str | None:
    """Extract the item search term from a natural-language query."""
    for pattern in _WHERE_PATTERNS:
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
    description = item.get("description", "").strip()

    parts = [f"**{name}**"]
    if location_name:
        parts.append(f"is in **{location_name}**")
    else:
        parts.append("has no location recorded")
    if description:
        parts.append(f"({description})")
    return " ".join(parts)


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

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a natural-language query about inventory."""
        text = user_input.text
        query = _extract_query(text)

        if query is None:
            # Fall back: treat the whole utterance as a search term
            query = text.strip()

        try:
            items = await self._api.async_search_items(query)
        except CannotConnectError:
            response_text = (
                "I couldn't reach Homebox right now. "
                "Please check that the add-on is running."
            )
        else:
            if not items:
                response_text = f"I couldn't find anything matching **{query}** in your inventory."
            elif len(items) == 1:
                response_text = f"I found one item: {_format_item(items[0])}."
            else:
                lines = "\n".join(f"- {_format_item(i)}" for i in items[:10])
                response_text = (
                    f"I found {len(items)} item(s) matching **{query}**:\n{lines}"
                )
                if len(items) > 10:
                    response_text += f"\n…and {len(items) - 10} more."

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)
        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id,
        )
