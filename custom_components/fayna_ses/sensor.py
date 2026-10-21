"""Power station measurements from Fayna SES."""

from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.helpers.entity import EntityCategory

from .api.const import BATTERY_STATES, CONNECTION_STATUSES, POWER_SOURCES
from .entity import FaynaSESEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import FaynaSESCoordinator

PARALLEL_UPDATES = 0

POWER_SENSORS = [
    SensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    )
    for key in (
        "grid_power",
        "battery_power",
        "solar_power",
        "building_power",
    )
]

ENERGY_SENSORS = [
    SensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
    )
    for key in ("solar_energy_today", "grid_energy_today", "building_energy_today")
]

SENSORS = (
    SensorEntityDescription(
        key="connection_status",
        translation_key="connection_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=[status.lower() for status in CONNECTION_STATUSES],
    ),
    SensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_state",
        translation_key="battery_state",
        device_class=SensorDeviceClass.ENUM,
        options=list(BATTERY_STATES),
    ),
    *POWER_SENSORS,
    SensorEntityDescription(
        key="last_update",
        translation_key="last_update",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    *ENERGY_SENSORS,
    SensorEntityDescription(
        key="power_source",
        translation_key="power_source",
        device_class=SensorDeviceClass.ENUM,
        options=list(POWER_SOURCES),
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry[FaynaSESCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add measurements for the configured power station."""
    async_add_entities(
        FaynaSESSensor(entry.runtime_data, description) for description in SENSORS
    )


class FaynaSESSensor(FaynaSESEntity, SensorEntity):
    """A measurement from the latest dashboard snapshot."""

    def __init__(
        self,
        coordinator: FaynaSESCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize a measurement description."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Keep diagnostic values visible without presenting stale telemetry."""
        return super().available and (
            self.entity_description.key in {"connection_status", "last_update"}
            or self.coordinator.is_fresh
        )

    @property
    def native_value(self) -> float | str | datetime | None:
        """Return a cached value, preserving missing measurements."""
        data = self.coordinator.data
        key = self.entity_description.key
        if key == "connection_status":
            status = data.status.lower() if data.status else None
            return status if status in self.entity_description.options else None
        if key == "last_update":
            return data.updated
        return getattr(data, key)

    @property
    def last_reset(self) -> datetime | None:
        """Use the source's Kyiv calendar day for daily energy meter cycles."""
        if (
            self.entity_description.device_class == SensorDeviceClass.ENERGY
            and self.native_value is not None
        ):
            return datetime.combine(
                self.coordinator.data.date,
                time.min,
                tzinfo=ZoneInfo("Europe/Kyiv"),
            )
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | float | None] | None:
        """Keep fixed equipment details together on the connection status."""
        if self.entity_description.key != "connection_status":
            return None
        data = self.coordinator.data
        return {
            "description": data.description,
            "inverter_kw": data.inverter_kw,
            "solar_capacity_kw": data.solar_capacity_kw,
            "battery_capacity_kwh": data.battery_capacity_kwh,
        }
