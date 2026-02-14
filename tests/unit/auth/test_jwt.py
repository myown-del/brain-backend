from datetime import datetime, timedelta, timezone

import pytest

from brain.domain.time import utc_now
from brain.application.abstractions.token_verifier import TokenExpiredError
from brain.infrastructure.jwt.service import JwtService


def test_jwt_expiration_calculation(freezer):
    current_time = utc_now()
    access_token_lifetime_seconds = 1000

    jwt_service = JwtService(
        secret_key="secret",
        access_token_lifetime=access_token_lifetime_seconds,
        algorithm="HS256",
    )

    payload = {"user_id": 1}
    jwt_token_encoded = jwt_service.create_token(payload=payload)

    expected_expires_at = current_time + timedelta(seconds=access_token_lifetime_seconds)
    expected_expires_at_timestamp = int(expected_expires_at.timestamp())

    real_expires_at_timestamp = int(jwt_token_encoded.expires_at.timestamp())
    assert real_expires_at_timestamp == expected_expires_at_timestamp
    assert jwt_token_encoded.expires_at.tzinfo == timezone.utc


def test_jwt_encoding_decoding(freezer):
    jwt_service = JwtService(
        secret_key="secret",
        access_token_lifetime=1000,
        algorithm="HS256",
    )

    payload = {"user_id": 1, "exp": 999999999999}
    jwt_token_encoded = jwt_service.create_token(payload=payload)

    jwt_token_decoded = jwt_service.decode_token(token=jwt_token_encoded.access_token)
    assert jwt_token_decoded == {"user_id": 1, "exp": 999999999999}


def test_jwt_token_expiration(freezer):
    access_token_lifetime_seconds = 1

    jwt_service = JwtService(
        secret_key="secret",
        access_token_lifetime=access_token_lifetime_seconds,
        algorithm="HS256",
    )

    payload = {"user_id": 1}
    jwt_token_encoded = jwt_service.create_token(payload=payload)

    tick_time = access_token_lifetime_seconds + 1
    freezer.tick(delta=timedelta(seconds=tick_time))

    with pytest.raises(TokenExpiredError):
        jwt_service.decode_token(token=jwt_token_encoded.access_token)
