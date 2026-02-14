from __future__ import annotations

from datetime import datetime, timezone
from typing import overload


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@overload
def ensure_utc_datetime(dt: datetime) -> datetime: ...


@overload
def ensure_utc_datetime(dt: None) -> None: ...


def ensure_utc_datetime(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None or dt.utcoffset() is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_iso_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    parsed = datetime.fromisoformat(normalized)
    parsed_utc = ensure_utc_datetime(parsed)
    return parsed_utc
