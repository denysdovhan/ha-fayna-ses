"""Home Assistant independent models for Fayna SES power station data."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import NamedTuple

from .const import (
    BATTERY_IDLE_POWER_W,
    BATTERY_STATE_CHARGING,
    BATTERY_STATE_DISCHARGING,
    BATTERY_STATE_IDLE,
    POWER_SOURCE_BATTERY,
    POWER_SOURCE_GRID,
    POWER_SOURCE_IDLE,
    POWER_SOURCE_SOLAR,
    POWER_SOURCE_THRESHOLD_W,
)


class FaynaSESApiError(Exception):
    """The dashboard feeds could not be fetched or parsed."""


class StationMetadata(NamedTuple):
    """Static power station details from the metadata feed."""

    name: str
    description: str
    inverter_kw: float | None
    solar_capacity_kw: float | None
    battery_capacity_kwh: float | None


class LatestMeasurements(NamedTuple):
    """The final aligned sample from today's feed."""

    sample_time: datetime | None
    battery_level: float | None
    solar_power: float | None
    grid_power: float | None
    battery_power: float | None
    building_power: float | None


@dataclass(frozen=True, slots=True)
class FaynaSESData:
    """A power station's metadata and latest reported measurements."""

    name: str
    description: str
    inverter_kw: float | None
    solar_capacity_kw: float | None
    battery_capacity_kwh: float | None
    status: str | None
    updated: datetime | None
    sample_time: datetime | None
    date: date
    battery_level: float | None
    solar_power: float | None
    grid_power: float | None
    battery_power: float | None
    building_power: float | None
    solar_energy_today: float | None
    grid_energy_today: float | None
    building_energy_today: float | None

    @property
    def battery_state(self) -> str | None:
        """Use the dashboard's signed power and 20 W idle band."""
        if self.battery_power is None:
            return None
        if self.battery_power > BATTERY_IDLE_POWER_W:
            return BATTERY_STATE_DISCHARGING
        if self.battery_power < -BATTERY_IDLE_POWER_W:
            return BATTERY_STATE_CHARGING
        return BATTERY_STATE_IDLE

    @property
    def power_source(self) -> str | None:
        """Match the dashboard's dominant-source heuristic, not mains presence."""
        power_values = (self.solar_power, self.grid_power, self.battery_power)
        has_readings = any(power is not None for power in power_values)
        if not has_readings:
            return None
        solar = self.solar_power or 0
        if solar > POWER_SOURCE_THRESHOLD_W and solar >= (self.building_power or 0):
            return POWER_SOURCE_SOLAR
        if (self.grid_power or 0) > POWER_SOURCE_THRESHOLD_W:
            return POWER_SOURCE_GRID
        if (self.battery_power or 0) > POWER_SOURCE_THRESHOLD_W:
            return POWER_SOURCE_BATTERY
        if solar > POWER_SOURCE_THRESHOLD_W:
            return POWER_SOURCE_SOLAR
        return POWER_SOURCE_IDLE
