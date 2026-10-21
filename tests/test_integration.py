"""Test entity behavior through Home Assistant's setup lifecycle."""

from dataclasses import replace
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fayna_ses.api import FaynaSESApiError, FaynaSESData
from custom_components.fayna_ses.const import CONF_STATION_ID, DOMAIN

from .conftest import STATION_ID

pytestmark = pytest.mark.freeze_time("2026-10-21T09:00:00Z")


async def setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Load a station through the real integration and entity platforms."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test power station",
        unique_id=STATION_ID,
        data={CONF_STATION_ID: STATION_ID},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def state(hass: HomeAssistant, key: str) -> State:
    """Find an entity by its stable unique ID, independent of translated names."""
    domain = "binary_sensor" if key == "connectivity" else "sensor"
    entity_id = er.async_get(hass).async_get_entity_id(
        domain, DOMAIN, f"{STATION_ID}_{key}"
    )
    assert entity_id is not None
    result = hass.states.get(entity_id)
    assert result is not None
    return result


async def test_setup_and_unload(hass: HomeAssistant, mock_fetch: AsyncMock) -> None:
    """Create all entities with correct units, signs, reset dates, and metadata."""
    entry = await setup_entry(hass)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    assert len(entities) == 13
    for entity in entities:
        key = entity.unique_id.removeprefix(f"{STATION_ID}_")
        expected_category = (
            "diagnostic"
            if key in {"last_update", "connection_status", "connectivity"}
            else None
        )
        assert entity.entity_category == expected_category
    assert (
        state(hass, "building_power").name
        == "Fayna SES — Test power station Building power"
    )
    assert (
        state(hass, "building_energy_today").name
        == "Fayna SES — Test power station Building energy today"
    )
    assert state(hass, "connectivity").state == "on"
    assert state(hass, "connection_status").state == "normal"
    assert state(hass, "battery_level").state == "75"
    assert state(hass, "battery_power").state == "-250"
    assert state(hass, "battery_state").state == "charging"
    assert state(hass, "power_source").state == "grid"
    assert state(hass, "building_power").attributes["unit_of_measurement"] == "W"
    assert state(hass, "last_update").state == "2026-10-21T09:00:00+00:00"
    for key, value in (
        ("solar_energy_today", "0"),
        ("grid_energy_today", "2.5"),
        ("building_energy_today", "1.5"),
    ):
        energy = state(hass, key)
        assert energy.state == value
        assert energy.attributes["state_class"] == "total"
        assert energy.attributes["last_reset"] == "2026-10-21T00:00:00+03:00"
    assert state(hass, "connection_status").attributes["battery_capacity_kwh"] == 60
    assert state(hass, "connection_status").attributes["solar_capacity_kw"] == 0
    mock_fetch.assert_awaited_once()
    coordinator = entry.runtime_data
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
    await hass.async_block_till_done()
    for entity in entities:
        remaining = hass.states.get(entity.entity_id)
        assert remaining is None or remaining.state == "unavailable"
    assert not tuple(coordinator.async_contexts())


async def test_setup_failure_retries(
    hass: HomeAssistant, mock_fetch: AsyncMock
) -> None:
    """The first failed fetch is retryable, not a permanently broken entry."""
    mock_fetch.side_effect = FaynaSESApiError("Unavailable")
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_STATION_ID: STATION_ID})
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_failure_and_recovery(
    hass: HomeAssistant, mock_fetch: AsyncMock, station_data: FaynaSESData
) -> None:
    """Failed polling makes entities unavailable and recovery restores values."""
    entry = await setup_entry(hass)
    mock_fetch.side_effect = FaynaSESApiError("Unavailable")
    await entry.runtime_data.async_refresh()
    assert state(hass, "battery_level").state == "unavailable"
    assert state(hass, "connectivity").state == "unavailable"
    mock_fetch.side_effect = None
    mock_fetch.return_value = replace(station_data, battery_level=80)
    await entry.runtime_data.async_refresh()
    assert state(hass, "battery_level").state == "80"
    assert state(hass, "connectivity").state == "on"


async def test_stale_and_null_readings(
    hass: HomeAssistant, mock_fetch: AsyncMock, station_data: FaynaSESData
) -> None:
    """Stale telemetry is unavailable and missing values never become zero."""
    entry = await setup_entry(hass)
    mock_fetch.return_value = replace(
        station_data,
        updated=station_data.updated - timedelta(minutes=31),
        sample_time=station_data.sample_time - timedelta(minutes=31),
    )
    await entry.runtime_data.async_refresh()
    assert state(hass, "building_power").state == "unavailable"
    assert state(hass, "connectivity").state == "unavailable"
    assert state(hass, "connection_status").state == "normal"
    assert state(hass, "last_update").state == "2026-10-21T08:29:00+00:00"
    mock_fetch.return_value = replace(
        station_data, building_power=None, battery_level=None
    )
    await entry.runtime_data.async_refresh()
    assert state(hass, "building_power").state == "unknown"
    assert state(hass, "battery_level").state == "unknown"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("PARTIAL_OFFLINE", "on"),
        ("ALL_OFFLINE", "off"),
        ("NO_DEVICE", "off"),
        (None, "unknown"),
    ],
)
async def test_connectivity_status(
    hass: HomeAssistant,
    mock_fetch: AsyncMock,
    station_data: FaynaSESData,
    status: str | None,
    expected: str,
) -> None:
    """Use provider connection status, independently of grid power."""
    mock_fetch.return_value = replace(station_data, status=status, grid_power=0)
    await setup_entry(hass)
    assert state(hass, "connectivity").state == expected


async def test_daily_reset_and_correction(
    hass: HomeAssistant, mock_fetch: AsyncMock, station_data: FaynaSESData
) -> None:
    """Corrections keep the cycle while a new source date changes last_reset."""
    entry = await setup_entry(hass)
    mock_fetch.return_value = replace(station_data, grid_energy_today=2.0)
    await entry.runtime_data.async_refresh()
    energy = state(hass, "grid_energy_today")
    assert energy.state == "2.0"
    assert energy.attributes["last_reset"] == "2026-10-21T00:00:00+03:00"
    mock_fetch.return_value = replace(
        station_data, date=station_data.date + timedelta(days=1), grid_energy_today=0
    )
    await entry.runtime_data.async_refresh()
    assert (
        state(hass, "grid_energy_today").attributes["last_reset"]
        == "2026-10-22T00:00:00+03:00"
    )


@pytest.mark.parametrize("status", ["ALL_OFFLINE", "NO_DEVICE"])
@pytest.mark.parametrize("missing_sample", [True, False])
async def test_offline_status_without_recent_measurements(
    hass: HomeAssistant,
    mock_fetch: AsyncMock,
    station_data: FaynaSESData,
    status: str,
    *,
    missing_sample: bool,
) -> None:
    """Fresh offline reports remain useful when telemetry has stopped."""
    mock_fetch.return_value = replace(
        station_data,
        status=status,
        sample_time=(
            None if missing_sample else station_data.sample_time - timedelta(minutes=31)
        ),
    )
    await setup_entry(hass)
    assert state(hass, "connectivity").state == "off"
    assert state(hass, "building_power").state == "unavailable"


@pytest.mark.parametrize(
    ("language", "prefix"),
    [("en", "Fayna SES"), ("uk", "Файна СЕС")],  # noqa: RUF001
)
@pytest.mark.usefixtures("mock_fetch")
async def test_localized_device_name(
    hass: HomeAssistant, language: str, prefix: str
) -> None:
    """Prefix station names using Home Assistant's configured language."""
    hass.config.language = language
    entry = await setup_entry(hass)
    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, STATION_ID), entry.entry_id
    )
    assert device is not None
    assert device.name == f"{prefix} — Test power station"
