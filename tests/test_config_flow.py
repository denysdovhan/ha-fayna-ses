"""Test dashboard URL setup and recovery."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fayna_ses.api import FaynaSESApiError
from custom_components.fayna_ses.const import (
    CONF_DASHBOARD_URL,
    CONF_STATION_ID,
    CUSTOM_DASHBOARD,
    DOMAIN,
    PRECONFIGURED_DASHBOARDS,
    REPORT_DASHBOARD_URL,
)

from .conftest import DASHBOARD_URL, STATION_ID


async def start_custom_flow(hass: HomeAssistant) -> ConfigFlowResult:
    """Choose custom setup through the public user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DASHBOARD_URL: CUSTOM_DASHBOARD}
    )


async def test_success(hass: HomeAssistant, mock_fetch: AsyncMock) -> None:
    """Test the form, validated station name, and stable unique identifier."""
    result = await start_custom_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "custom"
    with patch("custom_components.fayna_ses.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DASHBOARD_URL: DASHBOARD_URL}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test power station"
    assert result["data"] == {CONF_STATION_ID: STATION_ID}
    assert result["result"].unique_id == STATION_ID
    mock_fetch.assert_awaited_once()


@pytest.mark.parametrize("invalid_url", ["", "https://example.com/s/test", "not a URL"])
async def test_invalid_url_recovery(
    hass: HomeAssistant, mock_fetch: AsyncMock, invalid_url: str
) -> None:
    """Reject unsupported URLs without fetching and permit correction."""
    result = await start_custom_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DASHBOARD_URL: invalid_url}
    )
    assert result["errors"] == {CONF_DASHBOARD_URL: "invalid_url"}
    mock_fetch.assert_not_awaited()
    with patch("custom_components.fayna_ses.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DASHBOARD_URL: DASHBOARD_URL}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_connection_error_recovery(
    hass: HomeAssistant, mock_fetch: AsyncMock
) -> None:
    """A failed request leaves the form retryable."""
    mock_fetch.side_effect = FaynaSESApiError("Unavailable")
    result = await start_custom_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DASHBOARD_URL: DASHBOARD_URL}
    )
    assert result["errors"] == {"base": "cannot_connect"}
    mock_fetch.side_effect = None
    with patch("custom_components.fayna_ses.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DASHBOARD_URL: DASHBOARD_URL}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_duplicate(hass: HomeAssistant, mock_fetch: AsyncMock) -> None:
    """A trailing slash cannot create duplicate station entities."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=STATION_ID, data={CONF_STATION_ID: STATION_ID}
    )
    entry.add_to_hass(hass)
    result = await start_custom_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DASHBOARD_URL: f"{DASHBOARD_URL}/"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_fetch.assert_not_awaited()


async def test_dashboard_choices(hass: HomeAssistant) -> None:
    """Offer named presets and custom URLs without fetching every station."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    field = next(iter(result["data_schema"].schema))
    assert field.default() == ""
    selector = result["data_schema"].schema[CONF_DASHBOARD_URL]
    assert selector.config["custom_value"] is False
    assert selector.config["mode"] == "dropdown"
    assert selector.config["options"] == [*PRECONFIGURED_DASHBOARDS, CUSTOM_DASHBOARD]
    assert selector.config["translation_key"] == "dashboard"
    assert result["description_placeholders"] == {"report_url": REPORT_DASHBOARD_URL}


@pytest.mark.parametrize("station_id", PRECONFIGURED_DASHBOARDS)
async def test_preset_success(
    hass: HomeAssistant, mock_fetch: AsyncMock, station_id: str
) -> None:
    """A preset follows the same validation and entry creation as a custom URL."""
    with patch("custom_components.fayna_ses.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_DASHBOARD_URL: station_id},
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_STATION_ID: station_id}
    assert result["result"].unique_id == station_id
    mock_fetch.assert_awaited_once()
