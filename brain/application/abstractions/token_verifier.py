from typing import Protocol

from brain.domain.entities.jwt import JwtAccessToken


class TokenExpiredError(Exception):
    pass


class TokenInvalidError(Exception):
    pass


class TokenVerifier(Protocol):
    def create_token(self, payload: dict) -> JwtAccessToken: ...

    def decode_token(self, token: str) -> dict: ...
