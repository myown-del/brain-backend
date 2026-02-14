from datetime import date, datetime
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from brain.application.abstractions.repositories.drafts import IDraftsRepository
from brain.application.abstractions.repositories.models import DraftCreationStat
from brain.domain.entities.draft import Draft
from brain.infrastructure.db.mappers.drafts import map_draft_to_db, map_draft_to_dm
from brain.infrastructure.db.models.draft import DraftDB
from brain.infrastructure.db.models.hashtag import DraftHashtagDB
from brain.domain.time import ensure_utc_datetime, utc_now


class DraftsRepository(IDraftsRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def _apply_common_filters(
        stmt,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        hashtags: list[str] | None = None,
    ):
        stmt = stmt.where(DraftDB.user_id == user_id)
        from_date = ensure_utc_datetime(from_date)
        to_date = ensure_utc_datetime(to_date)
        if from_date:
            stmt = stmt.where(DraftDB.created_at >= from_date)
        if to_date:
            stmt = stmt.where(DraftDB.created_at <= to_date)
        if hashtags:
            stmt = (
                stmt.join(DraftHashtagDB, DraftHashtagDB.draft_id == DraftDB.id)
                .where(DraftHashtagDB.hashtag_text.in_(hashtags))
                .group_by(DraftDB.id)
                .having(func.count(func.distinct(DraftHashtagDB.hashtag_text)) == len(hashtags))
            )
        return stmt

    async def create(self, entity: Draft) -> None:
        db_model = map_draft_to_db(entity)
        self._session.add(db_model)
        await self._session.commit()

    async def get_by_id(self, draft_id: UUID) -> Draft | None:
        stmt = (
            select(DraftDB)
            .options(selectinload(DraftDB.hashtags))
            .where(DraftDB.id == draft_id)
        )
        result = await self._session.execute(stmt)
        db_model = result.scalar_one_or_none()
        if not db_model:
            return None
        return map_draft_to_dm(db_model)

    async def get_by_user(
        self,
        user_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        hashtags: list[str] | None = None,
    ) -> list[Draft]:
        stmt = select(DraftDB).options(selectinload(DraftDB.hashtags))
        stmt = self._apply_common_filters(
            stmt=stmt,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            hashtags=hashtags,
        )
        stmt = stmt.order_by(DraftDB.created_at.desc())
        result = await self._session.execute(stmt)
        db_models = result.unique().scalars().all()
        return [map_draft_to_dm(db_model) for db_model in db_models]

    async def search_by_text(
        self,
        user_id: UUID,
        query: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        hashtags: list[str] | None = None,
    ) -> list[Draft]:
        normalized_query = (query or "").strip().lower()
        if not normalized_query:
            return []

        stmt = (
            select(DraftDB)
            .options(selectinload(DraftDB.hashtags))
            .where(func.lower(func.coalesce(DraftDB.text, "")).like(f"%{normalized_query}%"))
        )
        stmt = self._apply_common_filters(
            stmt=stmt,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            hashtags=hashtags,
        )
        stmt = stmt.order_by(DraftDB.updated_at.desc())
        result = await self._session.execute(stmt)
        db_models = result.unique().scalars().all()
        return [map_draft_to_dm(db_model) for db_model in db_models]

    async def update(self, entity: Draft) -> None:
        stmt = select(DraftDB).where(DraftDB.id == entity.id)
        result = await self._session.execute(stmt)
        db_model = result.scalar_one_or_none()
        if db_model is None:
            return
        db_model.text = entity.text
        db_model.updated_at = ensure_utc_datetime(entity.updated_at) or utc_now()
        await self._session.commit()

    async def delete_by_id(self, draft_id: UUID) -> None:
        stmt = select(DraftDB).where(DraftDB.id == draft_id)
        result = await self._session.execute(stmt)
        db_model = result.scalar_one_or_none()
        if db_model is None:
            return
        await self._session.delete(db_model)
        await self._session.commit()

    async def delete_all(self) -> None:
        await self._session.execute(delete(DraftHashtagDB))
        await self._session.execute(text("DELETE FROM drafts"))
        await self._session.commit()

    async def get_draft_creation_stats_by_user_id(
        self,
        user_id: UUID,
        timezone_name: str = "UTC",
    ) -> list[DraftCreationStat]:
        created_date = func.date(func.timezone(timezone_name, DraftDB.created_at)).label(
            "created_date",
        )
        stmt = (
            select(created_date, func.count(DraftDB.id))
            .where(DraftDB.user_id == user_id)
            .group_by(created_date)
            .order_by(created_date.asc())
        )
        result = await self._session.execute(stmt)

        stats: list[DraftCreationStat] = []
        for created_at, count in result.all():
            if isinstance(created_at, str):
                created_at = date.fromisoformat(created_at)
            elif isinstance(created_at, datetime):
                created_at = created_at.date()
            stats.append(
                DraftCreationStat(
                    date=created_at,
                    count=int(count or 0),
                ),
            )
        return stats
