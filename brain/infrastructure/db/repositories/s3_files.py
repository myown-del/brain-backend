from uuid import UUID

from sqlalchemy import select, bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from brain.application.abstractions.repositories.s3_files import IS3FilesRepository
from brain.domain.entities.s3_file import S3File
from brain.infrastructure.db.mappers.s3_files import (
    map_s3_file_to_dm,
    map_s3_file_to_db,
)
from brain.infrastructure.db.models.s3 import S3FileDB
from brain.infrastructure.db.models.user import UserDB

class S3FilesRepository(IS3FilesRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: S3File) -> None:
        db_model = map_s3_file_to_db(entity)
        self._session.add(db_model)
        await self._session.flush()

    async def _get_db_by_id(self, entity_id: UUID) -> S3FileDB | None:
        query = select(S3FileDB).where(S3FileDB.id == bindparam("entity_id"))
        result = await self._session.execute(
            statement=query,
            params={"entity_id": entity_id},
        )
        return result.scalar()

    async def get_by_id(self, file_id: UUID) -> S3File | None:
        db_model = await self._get_db_by_id(entity_id=file_id)
        if db_model:
            return map_s3_file_to_dm(db_model)

    async def update(self, entity: S3File) -> None:
        old_db_model = await self._get_db_by_id(entity.id)
        old_db_model.name = entity.name
        old_db_model.path = entity.path
        old_db_model.content_type = entity.content_type
        await self._session.flush()

    async def get_by_user_id(self, user_id: UUID) -> S3File | None:
        query = (
            select(S3FileDB)
            .join(UserDB, UserDB.profile_picture_file_id == S3FileDB.id)
            .where(UserDB.id == user_id)
        )  # fmt: skip
        result = await self._session.execute(query)
        db_model = result.scalar()
        if db_model:
            return map_s3_file_to_dm(db_model)

    async def delete_all(self) -> None:
        await self._session.execute(text("DELETE FROM s3_files"))
        await self._session.flush()

