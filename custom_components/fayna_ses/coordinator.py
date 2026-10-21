"""Coordinate power station data updates."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import FaynaSESApi, FaynaSESApiError, FaynaSESData
from .const import DOMAIN, STALE_AFTER, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class FaynaSESCoordinator(DataUpdateCoordinator[FaynaSESData]):
    """Fetch one power station for all its entities."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: FaynaSESApi, station_id: str
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=UPDATE_INTERVAL,
            # Freshness changes even when the remote payload stays unchanged.
            always_update=True,
        )
        self.api = api
        self.station_id = station_id

    @property
    def is_source_fresh(self) -> bool:
        """Allow a current connection status even when measurements stop."""
        stamp = self.data.updated
        return (
            stamp is not None
            and -UPDATE_INTERVAL <= dt_util.utcnow() - stamp <= STALE_AFTER
        )

    @property
    def is_fresh(self) -> bool:
        """Require recent source and measurement timestamps."""
        now = dt_util.utcnow()
        return all(
            stamp is not None and -UPDATE_INTERVAL <= now - stamp <= STALE_AFTER
            for stamp in (self.data.updated, self.data.sample_time)
        )

    async def _async_update_data(self) -> FaynaSESData:
        """Fetch and validate current station data."""
        try:
            return await self.api.async_fetch()
        except FaynaSESApiError as err:
            message = "Unable to fetch Fayna SES data"
            raise UpdateFailed(message) from err


type FaynaSESConfigEntry = ConfigEntry[FaynaSESCoordinator]
