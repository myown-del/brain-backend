from dataclasses import asdict
from datetime import timedelta
from uuid import UUID, uuid4

from brain.application.interactors.users.get_user import GetUserInteractor
from brain.application.interactors.auth.dto import (
    JwtTokenCreationPayload,
    DecodedJwtTokenPayload,
)
from brain.application.interactors.auth.exceptions import JwtTokenExpiredException, JwtTokenInvalidException
from brain.application.abstractions.token_verifier import (
    TokenVerifier,
    TokenExpiredError,
    TokenInvalidError,
)
from brain.application.abstractions.repositories.jwt import (
    IJwtRefreshTokensRepository,
)

from brain.config.models import AuthenticationConfig
from brain.domain.entities.jwt import JwtAccessToken, FullJwtToken, JwtRefreshToken
from brain.domain.time import ensure_utc_datetime, utc_now
from brain.domain.entities.user import User


class AuthInteractor:
    def __init__(
        self,
        user_interactor: GetUserInteractor,
        auth_config: AuthenticationConfig,
        jwt_service: TokenVerifier,
        jwt_repo: IJwtRefreshTokensRepository,
    ):
        self._user_interactor = user_interactor
        self._auth_config = auth_config
        self._jwt_service = jwt_service
        self._jwt_repo = jwt_repo

    def _create_jwt_token(
        self,
        payload: JwtTokenCreationPayload,
    ) -> JwtAccessToken:
        return self._jwt_service.create_token(
            payload=asdict(payload),
        )

    def _create_access_token_for_user(self, user_id: UUID) -> JwtAccessToken:
        return self._create_jwt_token(
            payload=JwtTokenCreationPayload(
                user_id=user_id,
            ),
        )

    async def _create_refresh_token_for_user(self, user_id: UUID) -> JwtRefreshToken:
        refresh_expires_at = utc_now() + timedelta(
            seconds=self._auth_config.refresh_token_lifetime,
        )
        refresh_jwt = self._jwt_service.create_token(
            payload={
                "user_id": user_id,
                "exp": refresh_expires_at,
            },
        )
        refresh_token = JwtRefreshToken(
            id=uuid4(),
            user_id=user_id,
            token=refresh_jwt.access_token,
            expires_at=refresh_expires_at,
            created_at=utc_now(),
        )
        await self._jwt_repo.create(refresh_token)
        return refresh_token

    def _decode_jwt_token(self, token: str) -> DecodedJwtTokenPayload:
        try:
            data = self._jwt_service.decode_token(token)
        except TokenExpiredError:
            raise JwtTokenExpiredException()
        except TokenInvalidError:
            raise JwtTokenInvalidException()

        if isinstance(data.get("user_id"), str):
            data["user_id"] = UUID(data["user_id"])
        jwt_token_payload = DecodedJwtTokenPayload(**data)
        return jwt_token_payload

    async def _issue_tokens_for_user_id(self, user_id: UUID) -> tuple[FullJwtToken, UUID]:
        access_token = self._create_access_token_for_user(user_id)
        refresh_token = await self._create_refresh_token_for_user(user_id)
        return (
            FullJwtToken(
                access_token=access_token.access_token,
                expires_at=access_token.expires_at,
                refresh_token=refresh_token.token,
                refresh_expires_at=refresh_token.expires_at,
            ),
            refresh_token.id,
        )

    async def issue_refresh_token_for_telegram_id(
        self,
        telegram_id: int,
    ) -> JwtRefreshToken:
        user = await self._user_interactor.get_user_by_telegram_id(telegram_id)
        return await self._create_refresh_token_for_user(user.id)

    async def login(self, telegram_id: int) -> FullJwtToken:
        user = await self._user_interactor.get_user_by_telegram_id(telegram_id)
        tokens, _ = await self._issue_tokens_for_user_id(user.id)
        return tokens

    async def refresh_tokens(self, refresh_token: str) -> FullJwtToken:
        payload = self._decode_jwt_token(refresh_token)
        token_record = await self._jwt_repo.get_by_token(refresh_token)
        if not token_record:
            raise JwtTokenInvalidException()
        token_expires_at = ensure_utc_datetime(token_record.expires_at)
        if token_expires_at < utc_now():
            raise JwtTokenExpiredException()
        if token_record.user_id != payload.user_id:
            raise JwtTokenInvalidException()

        await self._jwt_repo.delete_by_id(token_record.id)
        tokens, _ = await self._issue_tokens_for_user_id(token_record.user_id)
        return tokens

    async def revoke_refresh_token(self, token_id: UUID) -> None:
        await self._jwt_repo.delete_by_id(token_id)

    async def build_tokens_for_refresh_token_id(
        self,
        token_id: UUID,
    ) -> FullJwtToken | None:
        refresh_token = await self._jwt_repo.get_by_id(token_id)
        if not refresh_token:
            return None
        refresh_expires_at = ensure_utc_datetime(refresh_token.expires_at)
        if refresh_expires_at < utc_now():
            return None

        access_token = self._create_access_token_for_user(refresh_token.user_id)
        return FullJwtToken(
            access_token=access_token.access_token,
            expires_at=access_token.expires_at,
            refresh_token=refresh_token.token,
            refresh_expires_at=refresh_token.expires_at,
        )

    async def authorize_by_token(self, token: str) -> User:
        payload = self._decode_jwt_token(token)
        user = await self._user_interactor.get_user_by_id(payload.user_id)
        return user
