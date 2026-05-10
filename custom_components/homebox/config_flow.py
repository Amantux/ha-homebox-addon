"""Config flow for Homebox integration."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnectError, HomeboxAPI, InvalidAuthError
from .const import CONF_TOKEN, CONF_URL, DEFAULT_NAME, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_TOKEN): str,
    }
)


class HomeboxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Homebox."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_URL])
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = HomeboxAPI(session, user_input[CONF_URL], user_input[CONF_TOKEN])
            try:
                await api.async_verify_auth()
            except InvalidAuthError:
                errors["base"] = "invalid_auth"
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
