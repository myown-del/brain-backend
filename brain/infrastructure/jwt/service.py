from datetime import datetime, timedelta
from json import JSONEncoder
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, DecodeError

from brain.application.abstractions.token_verifier import (
    TokenVerifier,
    TokenExpiredError,
    TokenInvalidError,
)
from brain.domain.entities.jwt import JwtAccessToken


class UUIDEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return obj.hex
        return JSONEncoder.default(self, obj)


class JwtService(TokenVerifier):
    def __init__(
        self,
        secret_key: str,
        access_token_lifetime: int,
        algorithm: str,
    ):
        self._secret_key = secret_key
        self._access_token_lifetime = access_token_lifetime
        self._algorithm = algorithm

    def create_token(self, payload: dict) -> JwtAccessToken:
        expires_at = payload.get("exp")
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(
                seconds=self._access_token_lifetime,
            )
            payload["exp"] = expires_at

        encoded_jwt = jwt.encode(
            payload=payload,
            key=self._secret_key,
            algorithm=self._algorithm,
            json_encoder=UUIDEncoder,
        )
        return JwtAccessToken(
            access_token=encoded_jwt,
            expires_at=expires_at,
        )

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                jwt=token,
                key=self._secret_key,
                algorithms=[self._algorithm],
            )
        except ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except DecodeError as exc:
            raise TokenInvalidError() from exc
