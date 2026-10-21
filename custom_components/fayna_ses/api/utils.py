"""Scalar validation helpers for external Fayna SES JSON values."""

import math
from datetime import UTC, datetime
from typing import Any


def parse_number(value: Any) -> float | None:
    """Accept a finite JSON number or null, never a boolean."""
    if value is None:
        return None
    if isinstance(value, bool):
        msg = "Boolean is not a numeric reading"
        raise TypeError(msg)
    if not isinstance(value, (int, float)):
        msg = "Expected a numeric reading"
        raise TypeError(msg)
    if not math.isfinite(value):
        msg = "Expected a finite numeric reading"
        raise ValueError(msg)
    return value


def parse_timestamp(value: Any) -> datetime | None:
    """Convert a nullable, non-negative UNIX timestamp to UTC."""
    seconds = parse_number(value)
    if seconds is None:
        return None
    if seconds < 0:
        msg = "Expected a non-negative timestamp"
        raise ValueError(msg)
    return datetime.fromtimestamp(seconds, UTC)


def require_object(value: Any) -> dict[str, Any]:
    """Require a JSON object before reading its fields."""
    if not isinstance(value, dict):
        msg = "Expected a JSON object"
        raise TypeError(msg)
    return value
