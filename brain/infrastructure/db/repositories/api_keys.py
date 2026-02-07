from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from brain.application.abstractions.repositories.api_keys import IApiKeysRepository
from brain.domain.entities.api_key import ApiKey
from brain.infrastructure.db.mappers.api_keys import (
    map_api_key_to_db,
    map_api_key_to_dm,
)
from brain.infrastructure.db.models.api_key import ApiKeyDB


class ApiKeysRepository(IApiKeysRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: ApiKey) -> None:
        db_model = map_api_key_to_db(entity)
        self._session.add(db_model)
        await self._session.commit()

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        query = select(ApiKeyDB).where(ApiKeyDB.key_hash == key_hash)
        result = await self._session.execute(query)
        db_model = result.scalar()
        if db_model:
            return map_api_key_to_dm(db_model)

    async def get_all_by_user_id(self, user_id: UUID) -> list[ApiKey]:
        query = select(ApiKeyDB).where(ApiKeyDB.user_id == user_id).order_by(ApiKeyDB.created_at.desc())
        result = await self._session.execute(query)
        db_models = result.scalars().all()
        return [map_api_key_to_dm(db_model) for db_model in db_models]

    async def delete_by_id_and_user_id(self, api_key_id: UUID, user_id: UUID) -> bool:
        stmt = delete(ApiKeyDB).where(
            ApiKeyDB.id == api_key_id,
            ApiKeyDB.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0
