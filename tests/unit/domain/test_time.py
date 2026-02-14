from datetime import datetime, timezone

from brain.domain.time import ensure_utc_datetime, parse_iso_datetime


def test_ensure_utc_datetime_makes_naive_datetime_aware() -> None:
    naive = datetime(2024, 1, 1, 12, 0, 0)
    converted = ensure_utc_datetime(naive)
    assert converted.tzinfo == timezone.utc


def test_ensure_utc_datetime_preserves_utc_datetime() -> None:
    aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    converted = ensure_utc_datetime(aware)
    assert converted == aware
    assert converted.tzinfo == timezone.utc


def test_parse_iso_datetime_accepts_z_suffix() -> None:
    parsed = parse_iso_datetime("2024-01-01T12:00:00Z")
    assert parsed.tzinfo == timezone.utc
