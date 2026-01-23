from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select, text, func, exists
from sqlalchemy.ext.asyncio import AsyncSession

from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.models import (
    WikilinkSuggestion,
    NoteCreationStat,
)
from brain.domain.entities.note import Note
from brain.infrastructure.db.mappers.notes import map_note_to_db, map_note_to_dm
from brain.infrastructure.db.models.keyword import KeywordDB
from brain.infrastructure.db.models.note import NoteDB
from brain.infrastructure.db.models.user import UserDB


class NotesRepository(INotesRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, entity: Note):
        db_model = map_note_to_db(entity)
        self._session.add(db_model)
        await self._session.commit()

    async def get_by_user_telegram_id(
        self,
        telegram_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Note]:
        query = (
            select(NoteDB)
            .join(UserDB)
            .where(UserDB.telegram_id == telegram_id)
        )  # fmt: skip
        if from_date:
            query = query.where(NoteDB.created_at >= from_date)
        if to_date:
            query = query.where(NoteDB.created_at <= to_date)
        result = await self._session.execute(query)

        db_models = result.unique().scalars().all()
        notes = [map_note_to_dm(db_model) for db_model in db_models]
        return notes

    async def get_by_id(self, note_id: UUID) -> Note | None:
        query = (
            select(NoteDB)
            .where(NoteDB.id == note_id)
        )  # fmt: skip
        result = await self._session.execute(query)
        db_model = result.scalar()
        if db_model:
            return map_note_to_dm(db_model)

    async def get_by_title(self, user_id: UUID, title: str, exact_match: bool = False) -> Note | None:
        query = (
            select(NoteDB)
            .where(NoteDB.user_id == user_id)
        )  # fmt: skip
        if exact_match:
            query = query.where(NoteDB.title == title)
        else:
            query = query.where(func.lower(NoteDB.title) == title.lower())

        result = await self._session.execute(query)
        db_model = result.scalar()
        if db_model:
            return map_note_to_dm(db_model)

    async def search_by_title(
        self,
        user_id: UUID,
        query: str,
        exact_match: bool = False,
    ) -> list[Note]:
        normalized = (query or "").strip()
        if not normalized:
            return []

        stmt = (
            select(NoteDB)
            .where(NoteDB.user_id == user_id)
            .where(NoteDB.title.isnot(None))
        )  # fmt: skip
        if exact_match:
            stmt = stmt.where(NoteDB.title == query)
        else:
            stmt = stmt.where(
                func.lower(func.trim(NoteDB.title)).like(f"%{normalized.lower()}%"),
            )

        stmt = stmt.order_by(NoteDB.updated_at.desc())
        result = await self._session.execute(stmt)
        db_models = result.scalars().all()
        return [map_note_to_dm(db_model) for db_model in db_models]

    async def update(self, entity: Note):
        query = (
            select(NoteDB)
            .where(NoteDB.id == entity.id)
        )  # fmt: skip
        result = await self._session.execute(query)
        db_model = result.scalar()
        if not db_model:
            return
        db_model.title = entity.title
        db_model.text = entity.text
        db_model.represents_keyword_id = entity.represents_keyword_id
        db_model.updated_at = entity.updated_at or datetime.utcnow()
        await self._session.commit()

    async def delete_all(self):
        await self._session.execute(text("DELETE FROM notes"))
        await self._session.commit()

    async def delete_by_id(self, entity_id: UUID):
        query = (
            select(NoteDB)
            .where(NoteDB.id == entity_id)
        )  # fmt: skip
        result = await self._session.execute(query)
        db_model = result.scalar()
        await self._session.delete(db_model)
        await self._session.commit()

    async def count_notes_by_user_and_title(
        self,
        user_id: UUID,
        title: str,
        exclude_note_id: UUID | None = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(NoteDB)
            .where(NoteDB.user_id == user_id)
            .where(NoteDB.title == title)
        )  # fmt: skip
        if exclude_note_id:
            query = query.where(NoteDB.id != exclude_note_id)
        result = await self._session.execute(query)
        return int(result.scalar() or 0)

    async def count_keyword_notes_by_user_and_title(
        self,
        user_id: UUID,
        title: str,
        exclude_note_id: UUID | None = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(NoteDB)
            .where(NoteDB.user_id == user_id)
            .where(NoteDB.title == title)
            .where(NoteDB.represents_keyword_id.isnot(None))
        )
        if exclude_note_id:
            query = query.where(NoteDB.id != exclude_note_id)
        result = await self._session.execute(query)
        return int(result.scalar() or 0)

    async def count_keyword_notes_by_user_and_keyword_id(
        self,
        user_id: UUID,
        keyword_id: UUID,
        exclude_note_id: UUID | None = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(NoteDB)
            .where(NoteDB.user_id == user_id)
            .where(NoteDB.represents_keyword_id == keyword_id)
        )
        if exclude_note_id:
            query = query.where(NoteDB.id != exclude_note_id)
        result = await self._session.execute(query)
        return int(result.scalar() or 0)

    async def search_wikilink_suggestions(
        self,
        user_id: UUID,
        query: str,
    ) -> list[WikilinkSuggestion]:
        normalized_query = query.strip().lower()
        if not normalized_query:
            return []

        keyword_note_stmt = (
            select(NoteDB.title)
            .where(NoteDB.user_id == user_id)
            .where(NoteDB.represents_keyword_id.isnot(None))
            .where(NoteDB.title.isnot(None))
            .where(func.length(func.trim(NoteDB.title)) > 0)
            .where(func.lower(NoteDB.title).like(f"%{normalized_query}%"))
            .order_by(NoteDB.title.asc())
        )
        keyword_result = await self._session.execute(keyword_note_stmt)

        seen: set[str] = set()
        suggestions: list[WikilinkSuggestion] = []

        for (title,) in keyword_result.all():
            if title is None:
                continue
            trimmed = title.strip()
            if not trimmed or trimmed in seen:
                continue
            seen.add(trimmed)
            suggestions.append(
                WikilinkSuggestion(
                    title=trimmed,
                    represents_keyword=True,
                ),
            )

        missing_note_stmt = (
            select(KeywordDB.name)
            .where(KeywordDB.user_id == user_id)
            .where(KeywordDB.name.isnot(None))
            .where(func.length(func.trim(KeywordDB.name)) > 0)
            .where(func.lower(KeywordDB.name).like(f"%{normalized_query}%"))
            .where(
                ~exists()
                .where(NoteDB.user_id == KeywordDB.user_id)
                .where(NoteDB.title == KeywordDB.name)
                .where(NoteDB.represents_keyword_id.isnot(None)),
            )
            .order_by(KeywordDB.name.asc())
        )
        missing_note_result = await self._session.execute(missing_note_stmt)

        for (name,) in missing_note_result.all():
            if name is None:
                continue
            trimmed = name.strip()
            if not trimmed or trimmed in seen:
                continue
            seen.add(trimmed)
            suggestions.append(
                WikilinkSuggestion(
                    title=trimmed,
                    represents_keyword=False,
                ),
            )
        return suggestions

    async def get_note_creation_stats_by_user_telegram_id(
        self,
        telegram_id: int,
    ) -> list[NoteCreationStat]:
        created_date = func.date(NoteDB.created_at).label("created_date")
        stmt = (
            select(created_date, func.count(NoteDB.id))
            .join(UserDB)
            .where(UserDB.telegram_id == telegram_id)
            .group_by(created_date)
            .order_by(created_date.asc())
        )
        result = await self._session.execute(stmt)

        stats: list[NoteCreationStat] = []
        for created_at, count in result.all():
            if isinstance(created_at, str):
                created_at = date.fromisoformat(created_at)
            elif isinstance(created_at, datetime):
                created_at = created_at.date()
            stats.append(
                NoteCreationStat(
                    date=created_at,
                    count=int(count or 0),
                ),
            )
        return stats
