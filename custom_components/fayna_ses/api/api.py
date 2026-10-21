"""Asynchronous client for the public Fayna SES feeds."""

import asyncio
from http import HTTPStatus
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import DATA_BASE_URL, REQUEST_TIMEOUT_SECONDS, STATION_ID_PATTERN
from .models import FaynaSESApiError, FaynaSESData
from .parse import parse_payloads


class FaynaSESApi:
    """Fetch public station data using the caller-owned HTTP session."""

    def __init__(self, session: ClientSession, station_id: str) -> None:
        """Initialize the client with a validated station identifier."""
        if STATION_ID_PATTERN.fullmatch(station_id) is None:
            msg = "Invalid station identifier"
            raise ValueError(msg)
        self._session = session
        self._station_id = station_id

    async def _async_fetch_json(self, filename: str) -> Any:
        """Fetch one feed without following redirects to unrelated hosts."""
        try:
            async with self._session.get(
                f"{DATA_BASE_URL}/{self._station_id}/{filename}",
                timeout=ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
                allow_redirects=False,
            ) as response:
                if response.status != HTTPStatus.OK:
                    msg = "Fayna SES feed is unavailable"
                    raise FaynaSESApiError(msg)
                return await response.json()
        except (ClientError, TimeoutError, ValueError):
            msg = "Unable to read Fayna SES feed"
            raise FaynaSESApiError(msg) from None

    async def async_fetch(self) -> FaynaSESData:
        """Fetch station metadata and today's measurements."""
        station, today = await asyncio.gather(
            self._async_fetch_json("station.json"),
            self._async_fetch_json("today.json"),
        )
        return parse_payloads(station, today)
