"""
Stub out homeassistant.* so the custom component can be imported and tested
without a full Home Assistant installation.
"""
import sys
import types
from unittest.mock import MagicMock


def _make_module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


# ---- base stubs ----
_ha = _make_module("homeassistant")
_make_module("homeassistant.core", HomeAssistant=MagicMock)
_make_module("homeassistant.const", Platform=MagicMock())


# ---- config_entries ----
class _ConfigEntry:
    def __init__(self, entry_id="test", data=None):
        self.entry_id = entry_id
        self.data = data or {}


class _ConfigFlow:
    pass


class _ConfigFlowResult:
    pass


_ce = _make_module(
    "homeassistant.config_entries",
    ConfigEntry=_ConfigEntry,
    ConfigFlow=_ConfigFlow,
    ConfigFlowResult=_ConfigFlowResult,
)

# ---- helpers ----
_make_module("homeassistant.helpers")
_make_module("homeassistant.helpers.aiohttp_client", async_get_clientsession=MagicMock())
_make_module("homeassistant.helpers.entity_platform", AddEntitiesCallback=MagicMock)


class _IntentResponse:
    def __init__(self, language="en"):
        self.language = language
        self.speech: dict = {}

    def async_set_speech(self, text: str) -> None:
        self.speech = {"plain": {"speech": text, "extra_data": None}}


_make_module("homeassistant.helpers.intent", IntentResponse=_IntentResponse)

# ---- conversation ----
class _ConversationInput:
    def __init__(self, text, language="en", conversation_id=None):
        self.text = text
        self.language = language
        self.conversation_id = conversation_id


class _ConversationResult:
    def __init__(self, response, conversation_id=None):
        self.response = response
        self.conversation_id = conversation_id


class _ConversationEntity:
    pass


class _AbstractConversationAgent:
    pass


_make_module(
    "homeassistant.components",
)
_make_module(
    "homeassistant.components.conversation",
    ConversationEntity=_ConversationEntity,
    AbstractConversationAgent=_AbstractConversationAgent,
    ConversationInput=_ConversationInput,
    ConversationResult=_ConversationResult,
)
