from brain.application.services.auth_tokens import AuthTokensService
from brain.domain.entities.jwt import FullJwtToken, JwtRefreshToken
from brain.domain.entities.user import User
from uuid import UUID


class AuthInteractor:
    def __init__(self, auth_tokens_service: AuthTokensService):
        self._auth_tokens_service = auth_tokens_service

    async def issue_refresh_token_for_telegram_id(self, telegram_id: int) -> JwtRefreshToken:
        return await self._auth_tokens_service.issue_refresh_token_for_telegram_id(telegram_id)

    async def login(self, telegram_id: int) -> FullJwtToken:
        return await self._auth_tokens_service.login(telegram_id)

    async def refresh_tokens(self, refresh_token: str) -> FullJwtToken:
        return await self._auth_tokens_service.refresh_tokens(refresh_token)

    async def revoke_refresh_token(self, token_id: UUID) -> None:
        await self._auth_tokens_service.revoke_refresh_token(token_id)

    async def build_tokens_for_refresh_token_id(self, token_id: UUID) -> FullJwtToken | None:
        return await self._auth_tokens_service.build_tokens_for_refresh_token_id(token_id)

    async def authorize_by_token(self, token: str) -> User:
        return await self._auth_tokens_service.authorize_by_token(token)
