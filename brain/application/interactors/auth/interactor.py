from brain.application.services.auth_tokens import AuthTokensService
from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.domain.entities.jwt import FullJwtToken, JwtRefreshToken
from brain.domain.entities.user import User
from uuid import UUID


class AuthInteractor:
    def __init__(
        self,
        auth_tokens_service: AuthTokensService,
        uow_factory: UnitOfWorkFactory,
    ):
        self._auth_tokens_service = auth_tokens_service
        self._uow_factory = uow_factory

    async def issue_refresh_token_for_telegram_id(self, telegram_id: int) -> JwtRefreshToken:
        async with self._uow_factory() as uow:
            token = await self._auth_tokens_service.issue_refresh_token_for_telegram_id(telegram_id)
            await uow.commit()
            return token

    async def login(self, telegram_id: int) -> FullJwtToken:
        async with self._uow_factory() as uow:
            tokens = await self._auth_tokens_service.login(telegram_id)
            await uow.commit()
            return tokens

    async def refresh_tokens(self, refresh_token: str) -> FullJwtToken:
        async with self._uow_factory() as uow:
            tokens = await self._auth_tokens_service.refresh_tokens(refresh_token)
            await uow.commit()
            return tokens

    async def revoke_refresh_token(self, token_id: UUID) -> None:
        async with self._uow_factory() as uow:
            await self._auth_tokens_service.revoke_refresh_token(token_id)
            await uow.commit()

    async def build_tokens_for_refresh_token_id(self, token_id: UUID) -> FullJwtToken | None:
        return await self._auth_tokens_service.build_tokens_for_refresh_token_id(token_id)

    async def authorize_by_token(self, token: str) -> User:
        return await self._auth_tokens_service.authorize_by_token(token)
