"""UI configuration for Fayna SES."""

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import FaynaSESApi, FaynaSESApiError, parse_dashboard_url
from .const import CONF_DASHBOARD_URL, CONF_STATION_ID, DOMAIN


class FaynaSESConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a power station using its dashboard URL."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate the dashboard and prevent duplicate power stations."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                station_id = parse_dashboard_url(user_input[CONF_DASHBOARD_URL])
            except ValueError:
                errors[CONF_DASHBOARD_URL] = "invalid_url"
            else:
                await self.async_set_unique_id(station_id)
                self._abort_if_unique_id_configured()
                api = FaynaSESApi(async_get_clientsession(self.hass), station_id)
                try:
                    data = await api.async_fetch()
                except FaynaSESApiError:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=data.name, data={CONF_STATION_ID: station_id}
                    )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DASHBOARD_URL): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.URL)
                    )
                }
            ),
            errors=errors,
        )
