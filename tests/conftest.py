"""Fixtures for Fayna SES integration tests."""

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.fayna_ses.api import FaynaSESData, parse_payloads

STATION_ID = "0123456789abcdef0123456789abcdef"
DASHBOARD_URL = f"https://fayna-ses.funs.net.ua/s/{STATION_ID}"


@pytest.fixture(autouse=True)
def enable_integration(enable_custom_integrations: None) -> None:
    """Allow loading the integration from this repository."""


@pytest.fixture
def station_data() -> FaynaSESData:
    """Return a coherent power station snapshot."""
    stamp = datetime(2026, 10, 21, 9, tzinfo=UTC).timestamp()
    return parse_payloads(
        {
            "name": "Test power station",
            "description": "Shared building loads",
            "inverterKw": 15,
            "pvKw": 0,
            "batteryKwh": 60,
        },
        {
            "date": "2026-10-21",
            "updated": stamp,
            "status": "NORMAL",
            "t": [stamp],
            "soc": [75],
            "pv": [0],
            "grid": [750],
            "batt": [-250],
            "load": [500],
            "day": {"pv": 0, "grid": 2.5, "load": 1.5},
        },
    )


@pytest.fixture
def mock_fetch(station_data: FaynaSESData) -> Generator[AsyncMock]:
    """Replace network requests with a validated snapshot."""
    with patch(
        "custom_components.fayna_ses.api.FaynaSESApi.async_fetch",
        return_value=station_data,
    ) as mock:
        yield mock
