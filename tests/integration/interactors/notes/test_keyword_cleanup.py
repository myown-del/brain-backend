import pytest
from dishka import AsyncContainer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from brain.application.interactors import CreateNoteInteractor, DeleteNoteInteractor
from brain.application.interactors.notes.dto import CreateNote
from brain.domain.entities.user import User
from brain.infrastructure.db.models.keyword import KeywordDB, NoteKeywordDB


@pytest.mark.asyncio
async def test_keywords_deleted_when_last_link_removed(
    dishka_request: AsyncContainer,
    user: User,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    delete_interactor = await dishka_request.get(DeleteNoteInteractor)
    session = await dishka_request.get(AsyncSession)

    first_note_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="First",
            text="See [[Omega]]",
        ),
    )
    second_note_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Second",
            text="Linking [[Omega]] too",
        ),
    )

    result = await session.execute(
        select(KeywordDB).where(KeywordDB.user_id == user.id, KeywordDB.name == "Omega"),
    )
    assert result.scalar() is not None

    await delete_interactor.delete_note(first_note_id)
    result = await session.execute(
        select(KeywordDB).where(KeywordDB.user_id == user.id, KeywordDB.name == "Omega"),
    )
    assert result.scalar() is not None

    await delete_interactor.delete_note(second_note_id)
    result = await session.execute(
        select(KeywordDB).where(KeywordDB.user_id == user.id, KeywordDB.name == "Omega"),
    )
    assert result.scalar() is None


@pytest.mark.asyncio
async def test_keyword_note_creates_keyword_without_link(
    dishka_request: AsyncContainer,
    user: User,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    delete_interactor = await dishka_request.get(DeleteNoteInteractor)
    session = await dishka_request.get(AsyncSession)

    note_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Atlas",
            text="No links here",
        ),
    )

    keyword_db = (
        await session.execute(
            select(KeywordDB).where(
                KeywordDB.user_id == user.id,
                KeywordDB.name == "Atlas",
            ),
        )
    ).scalar()
    assert keyword_db is not None

    link = (
        await session.execute(
            select(NoteKeywordDB).where(
                NoteKeywordDB.note_id == note_id,
                NoteKeywordDB.keyword_id == keyword_db.id,
            ),
        )
    ).scalar()
    assert link is None

    await delete_interactor.delete_note(note_id)

    keyword_after = (
        await session.execute(
            select(KeywordDB).where(
                KeywordDB.user_id == user.id,
                KeywordDB.name == "Atlas",
            ),
        )
    ).scalar()
    assert keyword_after is None
