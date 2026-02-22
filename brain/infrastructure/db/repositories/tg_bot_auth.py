from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from brain.application.abstractions.repositories.tg_bot_auth import (
    ITelegramBotAuthSessionsRepository,
)
from brain.domain.entities.tg_bot_auth import TelegramBotAuthSession
from brain.infrastructure.db.mappers.tg_bot_auth import (
    map_telegram_bot_auth_session_to_db,
    map_telegram_bot_auth_session_to_dm,
)
from brain.infrastructure.db.models.tg_bot_auth import (
    TelegramBotAuthSessionDB,
)


class TelegramBotAuthSessionsRepository(ITelegramBotAuthSessionsRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: TelegramBotAuthSession) -> None:
        db_model = map_telegram_bot_auth_session_to_db(entity)
        self._session.add(db_model)
        await self._session.flush()

    async def get_by_id(self, session_id: str) -> TelegramBotAuthSession | None:
        query = select(TelegramBotAuthSessionDB).where(
            TelegramBotAuthSessionDB.id == session_id,
        )
        result = await self._session.execute(query)
        db_model = result.scalar()
        if db_model:
            return map_telegram_bot_auth_session_to_dm(db_model)

    async def attach_user_if_empty(
        self,
        session_id: str,
        telegram_id: int,
        jwt_token_id: UUID,
    ) -> bool:
        stmt = (
            update(TelegramBotAuthSessionDB)
            .where(
                TelegramBotAuthSessionDB.id == session_id,
                TelegramBotAuthSessionDB.user_id.is_(None),
            )
            .values(user_id=telegram_id, jwt_token_id=jwt_token_id)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return bool(result.rowcount)

