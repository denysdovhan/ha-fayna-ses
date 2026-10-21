"""Test dashboard URL setup and recovery."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fayna_ses.api import FaynaSESApiError
from custom_components.fayna_ses.const import (
    CONF_DASHBOARD_URL,
    CONF_STATION_ID,
    DOMAIN,
)

from .conftest import DASHBOARD_URL, STATION_ID


async def test_success(hass: HomeAssistant, mock_fetch: AsyncMock) -> None:
    """Test the form, validated station name, and stable unique identifier."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
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


@pytest.mark.parametrize("invalid_url", ["https://example.com/s/test", "not a URL"])
async def test_invalid_url_recovery(
    hass: HomeAssistant, mock_fetch: AsyncMock, invalid_url: str
) -> None:
    """Reject unsupported URLs without fetching and permit correction."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_DASHBOARD_URL: invalid_url}
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
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_DASHBOARD_URL: DASHBOARD_URL},
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
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_DASHBOARD_URL: f"{DASHBOARD_URL}/"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_fetch.assert_not_awaited()
