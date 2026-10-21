"""Fayna SES power station integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FaynaSESApi
from .const import CONF_STATION_ID
from .coordinator import FaynaSESConfigEntry, FaynaSESCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: FaynaSESConfigEntry) -> bool:
    """Set up a power station from a config entry."""
    station_id = entry.data[CONF_STATION_ID]
    coordinator = FaynaSESCoordinator(
        hass, entry, FaynaSESApi(async_get_clientsession(hass), station_id), station_id
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FaynaSESConfigEntry) -> bool:
    """Unload the power station entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
