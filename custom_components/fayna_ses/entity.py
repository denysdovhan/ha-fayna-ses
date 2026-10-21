"""Shared entity information for a Fayna SES power station."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api.const import DASHBOARD_BASE_URL
from .const import DOMAIN
from .coordinator import FaynaSESCoordinator


class FaynaSESEntity(CoordinatorEntity[FaynaSESCoordinator]):
    """An entity using one power station's cached data."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FaynaSESCoordinator, key: str) -> None:
        """Set a stable identifier for the power station and measurement."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.station_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the power station represented by the dashboard."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.station_id)},
            translation_key="power_station",
            translation_placeholders={"name": self.coordinator.data.name},
            manufacturer="Fayna SES",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=f"{DASHBOARD_BASE_URL}/{self.coordinator.station_id}",
        )
