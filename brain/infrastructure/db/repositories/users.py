from uuid import UUID

from sqlalchemy import select, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from brain.application.abstractions.repositories.users import IUsersRepository
from brain.domain.entities.user import User
from brain.infrastructure.db.mappers.users import map_user_to_dm, map_user_to_db
from brain.infrastructure.db.models.user import UserDB
from brain.domain.time import utc_now


class UsersRepository(IUsersRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: User) -> None:
        db_model = map_user_to_db(entity)
        self._session.add(db_model)
        await self._session.flush()

    async def _get_db_by_id(self, entity_id: UUID) -> User | None:
        query = select(UserDB).where(UserDB.id == bindparam("entity_id"))
        result = await self._session.execute(
            statement=query,
            params={"entity_id": entity_id},
        )
        return result.scalar()

    async def update(self, entity: User) -> None:
        old_db_model = await self._get_db_by_id(entity.id)
        old_db_model.username = entity.username
        old_db_model.first_name = entity.first_name
        old_db_model.last_name = entity.last_name
        old_db_model.pin_hash = entity.pin_hash
        old_db_model.profile_picture_file_id = entity.profile_picture_file_id
        old_db_model.updated_at = utc_now()
        await self._session.flush()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        query = select(UserDB).where(UserDB.telegram_id == telegram_id)
        result = await self._session.execute(query)
        db_model = result.scalar()
        if db_model:
            return map_user_to_dm(db_model)

    async def get_by_id(self, entity_id: UUID) -> User | None:
        db_model = await self._get_db_by_id(entity_id)
        if db_model:
            return map_user_to_dm(db_model)

    async def delete_all(self) -> None:
        await self._session.execute(text("DELETE FROM users"))
        await self._session.flush()

    async def get_all(self) -> list[User]:
        query = select(UserDB)
        result = await self._session.execute(query)
        db_models = result.scalars().all()
        return [map_user_to_dm(db_model) for db_model in db_models]

