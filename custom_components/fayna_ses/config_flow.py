"""UI configuration for Fayna SES."""

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import FaynaSESApi, FaynaSESApiError, parse_dashboard_url
from .api.const import DASHBOARD_BASE_URL
from .const import (
    CONF_DASHBOARD_URL,
    CONF_STATION_ID,
    CUSTOM_DASHBOARD,
    DOMAIN,
    PRECONFIGURED_DASHBOARDS,
    REPORT_DASHBOARD_URL,
)


class FaynaSESConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a power station using its dashboard URL."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select a preset or open the custom URL form."""
        if user_input and user_input[CONF_DASHBOARD_URL] == CUSTOM_DASHBOARD:
            return await self.async_step_custom()
        return await self._async_configure_dashboard(user_input, "user")

    async def async_step_custom(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a station from its public URL."""
        return await self._async_configure_dashboard(user_input, "custom")

    async def _async_configure_dashboard(
        self, user_input: dict[str, Any] | None, step_id: str
    ) -> ConfigFlowResult:
        """Validate the dashboard and prevent duplicate power stations."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                dashboard = user_input[CONF_DASHBOARD_URL]
                if dashboard in PRECONFIGURED_DASHBOARDS:
                    dashboard = f"{DASHBOARD_BASE_URL}/{dashboard}"
                station_id = parse_dashboard_url(dashboard)
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
        selector = SelectSelector(
            SelectSelectorConfig(
                options=[*PRECONFIGURED_DASHBOARDS, CUSTOM_DASHBOARD],
                translation_key="dashboard",
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
        if step_id == "custom":
            selector = TextSelector(TextSelectorConfig(type=TextSelectorType.URL))
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {vol.Required(CONF_DASHBOARD_URL, default=""): selector}
            ),
            errors=errors,
            description_placeholders={"report_url": REPORT_DASHBOARD_URL},
        )
