"""Power station telemetry connectivity from Fayna SES."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.entity import EntityCategory

from .api.const import CONNECTED_STATUSES, DISCONNECTED_STATUSES
from .entity import FaynaSESEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import FaynaSESCoordinator

PARALLEL_UPDATES = 0


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry[FaynaSESCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the power station connection indicator."""
    async_add_entities([FaynaSESConnectivity(entry.runtime_data)])


class FaynaSESConnectivity(FaynaSESEntity, BinarySensorEntity):
    """Report telemetry connectivity, not mains availability."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "connectivity"

    def __init__(self, coordinator: FaynaSESCoordinator) -> None:
        """Initialize the connection indicator."""
        super().__init__(coordinator, "connectivity")

    @property
    def available(self) -> bool:
        """Require fresh data before interpreting connection status."""
        return super().available and self.coordinator.is_source_fresh

    @property
    def is_on(self) -> bool | None:
        """Return the provider's connection state when recognized."""
        status = self.coordinator.data.status
        if status in CONNECTED_STATUSES:
            return True
        if status in DISCONNECTED_STATUSES:
            return False
        return None
