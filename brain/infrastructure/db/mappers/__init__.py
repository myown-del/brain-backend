from datetime import datetime

from brain.domain.time import ensure_utc_datetime


def normalize_datetime(value: datetime | None) -> datetime | None:
    return ensure_utc_datetime(value)
