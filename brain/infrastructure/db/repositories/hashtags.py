from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from brain.application.abstractions.repositories.hashtags import IHashtagsRepository
from brain.domain.entities.hashtag import Hashtag
from brain.infrastructure.db.models.hashtag import DraftHashtagDB, HashtagDB


class HashtagsRepository(IHashtagsRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def ensure_hashtags(self, texts: list[str]) -> None:
        if not texts:
            return
        stmt = insert(HashtagDB).values(
            [{"text": text} for text in texts],
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["text"])
        await self._session.execute(stmt)
        await self._session.commit()

    async def replace_draft_hashtags(self, draft_id: UUID, texts: list[str]) -> None:
        await self._session.execute(
            delete(DraftHashtagDB).where(DraftHashtagDB.draft_id == draft_id),
        )
        if not texts:
            await self._session.commit()
            return

        await self.ensure_hashtags(texts=texts)

        insert_stmt = insert(DraftHashtagDB).values(
            [{"draft_id": draft_id, "hashtag_text": text} for text in texts],
        )
        insert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["draft_id", "hashtag_text"])
        await self._session.execute(insert_stmt)
        await self._session.commit()

    async def get_draft_hashtags(self, draft_id: UUID) -> list[str]:
        stmt = (
            select(DraftHashtagDB.hashtag_text)
            .where(DraftHashtagDB.draft_id == draft_id)
            .order_by(DraftHashtagDB.hashtag_text.asc())
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all() if row[0]]

    async def get_by_text(self, text: str) -> Hashtag | None:
        stmt = select(HashtagDB).where(HashtagDB.text == text)
        result = await self._session.execute(stmt)
        db_model = result.scalar_one_or_none()
        if not db_model:
            return None
        return Hashtag(
            text=db_model.text,
            created_at=db_model.created_at,
        )
