"""Validate the public metadata and daily telemetry feed schemas."""

from datetime import date, datetime
from itertools import pairwise
from typing import Any

from .const import DASHBOARD_URL_PATTERN, MAX_BATTERY_LEVEL
from .models import FaynaSESApiError, FaynaSESData, LatestMeasurements, StationMetadata
from .utils import parse_number, parse_timestamp, require_object


def parse_dashboard_url(url: str) -> str:
    """Extract a station identifier only from a supported dashboard URL."""
    match = DASHBOARD_URL_PATTERN.fullmatch(url.strip())
    if match is None:
        msg = "Enter a Fayna SES power station dashboard URL"
        raise ValueError(msg)
    return match[1]


def _parse_station(payload: Any) -> StationMetadata:
    """Validate the station's label, description and equipment capacities."""
    station = require_object(payload)
    name, description = station["name"], station["description"]
    if not isinstance(name, str) or not name.strip():
        raise TypeError
    if not isinstance(description, str):
        raise TypeError
    return StationMetadata(
        name=name,
        description=description,
        inverter_kw=parse_number(station.get("inverterKw")),
        solar_capacity_kw=parse_number(station["pvKw"]),
        battery_capacity_kwh=parse_number(station.get("batteryKwh")),
    )


def _parse_status(value: Any) -> str | None:
    """Preserve provider status strings, including newly introduced values."""
    if value is not None and not isinstance(value, str):
        raise TypeError
    return value


def _parse_timestamps(values: Any) -> list[datetime]:
    """Validate non-null sample timestamps in chronological order."""
    if not isinstance(values, list):
        raise TypeError
    timestamps = []
    for value in values:
        timestamp = parse_timestamp(value)
        if timestamp is None:
            raise ValueError
        timestamps.append(timestamp)
    if any(left > right for left, right in pairwise(values)):
        raise ValueError
    return timestamps


def _latest_reading(values: Any, sample_count: int) -> float | None:
    """Validate alignment and all readings before selecting the final value."""
    if not isinstance(values, list) or len(values) != sample_count:
        raise ValueError
    readings = [parse_number(value) for value in values]
    return readings[-1] if readings else None


def _parse_measurements(today: dict[str, Any]) -> LatestMeasurements:
    """Extract the latest aligned measurements without replacing missing values."""
    timestamps = _parse_timestamps(today["t"])
    sample_count = len(timestamps)
    battery_level = _latest_reading(today["soc"], sample_count)
    if battery_level is not None and not 0 <= battery_level <= MAX_BATTERY_LEVEL:
        raise ValueError
    return LatestMeasurements(
        sample_time=timestamps[-1] if timestamps else None,
        battery_level=battery_level,
        solar_power=_latest_reading(today["pv"], sample_count),
        grid_power=_latest_reading(today["grid"], sample_count),
        battery_power=_latest_reading(today["batt"], sample_count),
        building_power=_latest_reading(today["load"], sample_count),
    )


def _assemble_snapshot(station: Any, today: Any) -> FaynaSESData:
    """Assemble a snapshot from the validated parts of each feed."""
    metadata = _parse_station(station)
    today = require_object(today)
    latest = _parse_measurements(today)
    energy = require_object(today["day"])
    return FaynaSESData(
        name=metadata.name,
        description=metadata.description,
        inverter_kw=metadata.inverter_kw,
        solar_capacity_kw=metadata.solar_capacity_kw,
        battery_capacity_kwh=metadata.battery_capacity_kwh,
        status=_parse_status(today["status"]),
        updated=parse_timestamp(today["updated"]),
        sample_time=latest.sample_time,
        date=date.fromisoformat(today["date"]),
        battery_level=latest.battery_level,
        solar_power=latest.solar_power,
        grid_power=latest.grid_power,
        battery_power=latest.battery_power,
        building_power=latest.building_power,
        solar_energy_today=parse_number(energy["pv"]),
        grid_energy_today=parse_number(energy.get("grid")),
        building_energy_today=parse_number(energy["load"]),
    )


def parse_payloads(station: Any, today: Any) -> FaynaSESData:
    """Validate feeds and select the final sample, preserving missing values."""
    try:
        return _assemble_snapshot(station, today)
    except (KeyError, TypeError, ValueError, OverflowError, OSError):
        msg = "Invalid Fayna SES response"
        raise FaynaSESApiError(msg) from None
