"""Tests for public feed parsing and the HTTP client."""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientConnectionError

from custom_components.fayna_ses.api import (
    FaynaSESApi,
    FaynaSESApiError,
    parse_dashboard_url,
    parse_payloads,
)

STATION_ID = "0123456789abcdef0123456789abcdef"
URL = f"https://fayna-ses.funs.net.ua/s/{STATION_ID}"
STATION = {
    "name": "Power station",
    "description": "Entrances 5-8",
    "inverterKw": 15,
    "pvKw": 0,
    "batteryKwh": 60,
}
TODAY = {
    "date": "2026-10-21",
    "updated": 1792531386,
    "status": "NORMAL",
    "t": [1792531011, 1792531386],
    "pv": [0, 0],
    "load": [537, 539],
    "grid": [540, 534],
    "batt": [70, 70],
    "soc": [99, 99],
    "day": {"pv": 0, "load": 0.1, "grid": 0.1},
}


@pytest.mark.parametrize("suffix", ["", "/"])
def test_dashboard_url(suffix: str) -> None:
    """Extract the ID from supported share URLs."""
    assert parse_dashboard_url(f" {URL}{suffix} ") == STATION_ID


@pytest.mark.parametrize(
    "url",
    [
        URL.replace("https:", "http:"),
        URL.replace("fayna-ses", "data-ses"),
        URL.replace("fayna-ses.funs.net.ua", "fayna-ses.funs.net.ua.evil.test"),
        URL.replace("https://", "https://user:pass@"),
        URL.replace(".ua/s/", ".ua:443/s/"),
        URL + "?token=secret",
        URL + "#fragment",
        URL + "/today.json",
        URL[:-1],
        URL.replace(STATION_ID, "../station"),
    ],
)
def test_reject_invalid_urls(url: str) -> None:
    """Never turn arbitrary URLs into network requests."""
    with pytest.raises(ValueError, match="dashboard URL"):
        parse_dashboard_url(url)


def test_latest_data() -> None:
    """Keep native units, timestamps, capacities and daily totals."""
    data = parse_payloads(STATION, TODAY)
    assert data.name == "Power station"
    assert data.inverter_kw == 15
    assert data.battery_capacity_kwh == 60
    assert data.solar_capacity_kw == 0
    assert data.date == date(2026, 10, 21)
    assert data.updated == datetime(2026, 10, 20, 21, 23, 6, tzinfo=UTC)
    assert data.sample_time == data.updated
    assert data.battery_level == 99
    assert data.building_power == 539
    assert data.grid_power == 534
    assert data.battery_power == 70
    assert data.solar_energy_today == 0
    assert data.grid_energy_today == data.building_energy_today == 0.1
    assert data.battery_state == "discharging"
    assert data.power_source == "grid"


def test_null_latest_is_not_old_value() -> None:
    """Do not substitute a stale sample or zero for a missing reading."""
    payload = deepcopy(TODAY)
    for key in ("pv", "load", "grid", "batt", "soc"):
        payload[key][-1] = None
    payload["updated"] = None
    payload["status"] = None
    payload["day"] = {"pv": None, "load": None}
    data = parse_payloads(STATION, payload)
    assert data.battery_level is None
    assert data.building_power is None
    assert data.grid_power is None
    assert data.battery_state is None
    assert data.power_source is None
    assert data.updated is None
    assert data.status is None
    assert data.grid_energy_today is None


def test_empty_day() -> None:
    """A valid day without measurements has unknown current readings."""
    payload = deepcopy(TODAY)
    for key in ("t", "pv", "load", "grid", "batt", "soc"):
        payload[key] = []
    data = parse_payloads(STATION, payload)
    assert data.sample_time is None
    assert data.battery_level is None


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("t", [1792531386, 1792531011]),
        ("t", [1792531011, None]),
        ("t", [1792531011, True]),
        ("grid", [534]),
        ("grid", [0, "534"]),
        ("grid", [0, True]),
        ("grid", [0, float("nan")]),
        ("grid", [0, float("inf")]),
        ("grid", "534"),
        ("soc", [99, 101]),
        ("soc", [99, -1]),
        ("updated", -1),
        ("updated", 10**100),
        ("date", "not-a-date"),
        ("status", True),
        ("day", []),
    ],
)
def test_invalid_telemetry(key: str, value: object) -> None:
    """Reject malformed data at the API boundary."""
    payload = deepcopy(TODAY)
    payload[key] = value
    with pytest.raises(FaynaSESApiError, match="Invalid Fayna SES response"):
        parse_payloads(STATION, payload)


def test_missing_required_field() -> None:
    """An absent array is an invalid response, not a zero measurement."""
    payload = deepcopy(TODAY)
    del payload["grid"]
    with pytest.raises(FaynaSESApiError):
        parse_payloads(STATION, payload)


@pytest.mark.parametrize(
    "station", [None, [], {**STATION, "name": ""}, {**STATION, "pvKw": True}]
)
def test_invalid_station(station: object) -> None:
    """Validate metadata alongside telemetry."""
    with pytest.raises(FaynaSESApiError):
        parse_payloads(station, TODAY)


@pytest.mark.parametrize(
    ("power", "expected"),
    [
        (-21, "charging"),
        (-20, "idle"),
        (0, "idle"),
        (20, "idle"),
        (21, "discharging"),
        (None, None),
    ],
)
def test_battery_state(power: float | None, expected: str | None) -> None:
    """Match charging directions and the dashboard idle deadband."""
    data = replace(parse_payloads(STATION, TODAY), battery_power=power)
    assert data.battery_state == expected


@pytest.mark.parametrize(
    ("solar", "grid", "battery", "load", "expected"),
    [
        (600, 100, 100, 500, "solar"),
        (100, 400, 100, 500, "grid"),
        (100, 0, 400, 500, "battery"),
        (100, 0, 0, 500, "solar"),
        (50, 50, 50, 150, "idle"),
        (0, -100, -100, 0, "idle"),
        (None, None, None, 500, None),
    ],
)
def test_power_source(
    solar: float | None,
    grid: float | None,
    battery: float | None,
    load: float,
    expected: str | None,
) -> None:
    """Preserve the dashboard source precedence and 50 W threshold."""
    data = replace(
        parse_payloads(STATION, TODAY),
        solar_power=solar,
        grid_power=grid,
        battery_power=battery,
        building_power=load,
    )
    assert data.power_source == expected


@pytest.mark.asyncio
async def test_fetch() -> None:
    """Fetch only fixed public endpoints using the supplied session."""
    session = MagicMock()
    responses = []
    for payload in (STATION, TODAY):
        response = MagicMock(status=200)
        response.json = AsyncMock(return_value=payload)
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=response)
        responses.append(context)
    session.get.side_effect = responses
    data = await FaynaSESApi(session, STATION_ID).async_fetch()
    assert data.battery_level == 99
    assert [call.args[0] for call in session.get.call_args_list] == [
        f"https://data-ses.funs.net.ua/s/{STATION_ID}/station.json",
        f"https://data-ses.funs.net.ua/s/{STATION_ID}/today.json",
    ]
    assert all(
        not call.kwargs["allow_redirects"] for call in session.get.call_args_list
    )


@pytest.mark.parametrize("status", [301, 403, 404, 429, 500])
@pytest.mark.asyncio
async def test_http_errors(status: int) -> None:
    """Reject failed responses and redirects without disclosing the share ID."""
    session = MagicMock()
    session.get.return_value.__aenter__ = AsyncMock(
        return_value=MagicMock(status=status)
    )
    with pytest.raises(FaynaSESApiError) as error:
        await FaynaSESApi(session, STATION_ID).async_fetch()
    assert STATION_ID not in str(error.value)


@pytest.mark.parametrize(
    "error",
    [ClientConnectionError("secret URL"), TimeoutError(), ValueError("bad JSON")],
)
@pytest.mark.asyncio
async def test_network_and_json_errors(error: Exception) -> None:
    """Normalize transport and decoding errors without leaking request URLs."""
    session = MagicMock()
    response = MagicMock(status=200)
    response.json = AsyncMock(side_effect=error)
    session.get.return_value.__aenter__ = AsyncMock(return_value=response)
    with pytest.raises(FaynaSESApiError, match="Unable to read Fayna SES feed"):
        await FaynaSESApi(session, STATION_ID).async_fetch()
