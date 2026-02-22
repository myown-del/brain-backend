from uuid import uuid4

from brain.application.abstractions.repositories.tg_bot_auth import ITelegramBotAuthSessionsRepository
from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.interactors.auth.dto import TelegramBotAuthSessionTokens
from brain.application.interactors.auth.exceptions import TelegramBotAuthSessionNotFoundException
from brain.application.services.auth_tokens import AuthTokensService
from brain.domain.entities.tg_bot_auth import TelegramBotAuthSession


class TelegramBotAuthSessionInteractor:
    def __init__(
        self,
        sessions_repo: ITelegramBotAuthSessionsRepository,
        auth_tokens_service: AuthTokensService,
        uow_factory: UnitOfWorkFactory,
    ):
        self._sessions_repo = sessions_repo
        self._auth_tokens_service = auth_tokens_service
        self._uow_factory = uow_factory

    def _generate_session_id(self) -> str:
        return uuid4().hex[:16]

    async def create_session(self) -> TelegramBotAuthSession:
        async with self._uow_factory() as uow:
            session_id = self._generate_session_id()
            for _ in range(5):
                existing = await self._sessions_repo.get_by_id(session_id)
                if not existing:
                    session = TelegramBotAuthSession(id=session_id, telegram_id=None)
                    await self._sessions_repo.create(session)
                    await uow.commit()
                    return session
                session_id = self._generate_session_id()

            session = TelegramBotAuthSession(id=session_id, telegram_id=None)
            await self._sessions_repo.create(session)
            await uow.commit()
            return session

    async def get_session(self, session_id: str) -> TelegramBotAuthSession:
        session = await self._sessions_repo.get_by_id(session_id)
        if not session:
            raise TelegramBotAuthSessionNotFoundException()
        return session

    async def attach_user_to_session(self, session_id: str, telegram_id: int) -> bool:
        async with self._uow_factory() as uow:
            refresh_token = await self._auth_tokens_service.issue_refresh_token_for_telegram_id(telegram_id)
            updated = await self._sessions_repo.attach_user_if_empty(
                session_id=session_id,
                telegram_id=telegram_id,
                jwt_token_id=refresh_token.id,
            )
            if not updated:
                await self._auth_tokens_service.revoke_refresh_token(refresh_token.id)
            await uow.commit()
            return updated

    async def get_session_with_tokens(self, session_id: str) -> TelegramBotAuthSessionTokens:
        session = await self.get_session(session_id)
        if not session.jwt_token_id:
            return TelegramBotAuthSessionTokens(session=session, tokens=None)

        tokens = await self._auth_tokens_service.build_tokens_for_refresh_token_id(session.jwt_token_id)
        return TelegramBotAuthSessionTokens(session=session, tokens=tokens)
