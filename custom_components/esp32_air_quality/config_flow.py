"""Config flow to configure the WLED integration."""
from __future__ import annotations

from typing import Any
import re

import voluptuous as vol

from .esp32aq import Esp32AirQuality, Esp32AQError

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER as logger

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)

IP_PATTERN = re.compile(
    "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
)
HOST_PATTERN = re.compile(
    "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
)


class ESP32FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a esp32 air quality config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        return await self._handle_config_flow(user_input)

    async def _handle_config_flow(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Config flow handler for WLED."""

        # Request user input, unless we are preparing discovery flow
        if user_input is None:
            return self._show_setup_form()

        # Validate input
        if self._validate_host(user_input[CONF_HOST]) is False:
            return self._show_setup_form({"base": "invalid_host"})

        # Connect to device via integration lib
        if user_input.get(CONF_MAC) is None:
            session = async_get_clientsession(self.hass)
            device = Esp32AirQuality(user_input[CONF_HOST], session=session)
            try:
                await device.connect()
                info = device.get_device_info()
            except Esp32AQError as error:
                logger.error("error connecting to %s: %s", user_input[CONF_HOST], error)
                return self._show_setup_form({"base": "cannot_connect"})
            user_input[CONF_MAC] = info.mac_address

        # Check if already configured
        await self.async_set_unique_id(user_input[CONF_MAC])
        self._abort_if_unique_id_configured()

        title = user_input[CONF_HOST]

        return self.async_create_entry(
            title=title,
            data={
                CONF_HOST: user_input[CONF_HOST],
                CONF_MAC: user_input[CONF_MAC],
            },
        )

    def _show_setup_form(self, errors: dict | None = None) -> FlowResult:
        """Show the setup form to the user."""

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors or {},
        )

    def _validate_host(self, host: str) -> bool:
        """Validate device host"""
        logger.info(host)
        return (IP_PATTERN.match(host) is not None) or (
            HOST_PATTERN.match(host) is not None
        )
