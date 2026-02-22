from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from brain.application.abstractions.repositories.jwt import (
    IJwtRefreshTokensRepository,
)
from brain.domain.entities.jwt import JwtRefreshToken
from brain.infrastructure.db.mappers.jwt import (
    map_jwt_refresh_token_to_db,
    map_jwt_refresh_token_to_dm,
)
from brain.infrastructure.db.models.jwt import JwtRefreshTokenDB


class JwtRefreshTokensRepository(IJwtRefreshTokensRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: JwtRefreshToken) -> None:
        db_model = map_jwt_refresh_token_to_db(entity)
        self._session.add(db_model)
        await self._session.flush()

    async def get_by_id(self, token_id: UUID) -> JwtRefreshToken | None:
        query = select(JwtRefreshTokenDB).where(JwtRefreshTokenDB.id == token_id)
        result = await self._session.execute(query)
        db_model = result.scalar()
        if db_model:
            return map_jwt_refresh_token_to_dm(db_model)

    async def get_by_token(self, token: str) -> JwtRefreshToken | None:
        query = select(JwtRefreshTokenDB).where(JwtRefreshTokenDB.token == token)
        result = await self._session.execute(query)
        db_model = result.scalar()
        if db_model:
            return map_jwt_refresh_token_to_dm(db_model)

    async def delete_by_id(self, token_id: UUID) -> None:
        stmt = delete(JwtRefreshTokenDB).where(JwtRefreshTokenDB.id == token_id)
        await self._session.execute(stmt)
        await self._session.flush()

