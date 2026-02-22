from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from dishka import AsyncContainer

from brain.application.interactors import GetNotesInteractor
from brain.domain.entities.note import Note
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from tests.integration.utils.uow import commit_repo_hub


async def _create_note_with_created_at(
    repo_hub: RepositoryHub,
    user: User,
    title: str,
    created_at: datetime,
) -> Note:
    await repo_hub.keywords.ensure_keywords(user.id, [title])
    keyword = await repo_hub.keywords.get_by_user_and_name(user.id, title)
    note = Note(
        id=uuid4(),
        user_id=user.id,
        title=title,
        text=f"{title} text",
        represents_keyword_id=keyword.id,
        created_at=created_at,
        updated_at=created_at,
        link_intervals=[],
    )
    await repo_hub.notes.create(note)
    await commit_repo_hub(repo_hub)
    return note


@pytest.mark.asyncio
async def test_get_notes_filters_from_date(
    dishka_request: AsyncContainer,
    repo_hub: RepositoryHub,
    user: User,
):
    interactor = await dishka_request.get(GetNotesInteractor)
    base = datetime(2024, 1, 1, 12, 0, 0)
    await _create_note_with_created_at(repo_hub, user, "Old", base)
    await _create_note_with_created_at(repo_hub, user, "New", base + timedelta(days=10))

    notes = await interactor.get_notes(
        user.telegram_id,
        from_date=base + timedelta(days=5),
    )

    assert {note.title for note in notes} == {"New"}


@pytest.mark.asyncio
async def test_get_notes_filters_to_date(
    dishka_request: AsyncContainer,
    repo_hub: RepositoryHub,
    user: User,
):
    interactor = await dishka_request.get(GetNotesInteractor)
    base = datetime(2024, 1, 1, 12, 0, 0)
    await _create_note_with_created_at(repo_hub, user, "Old", base)
    await _create_note_with_created_at(repo_hub, user, "New", base + timedelta(days=10))

    notes = await interactor.get_notes(
        user.telegram_id,
        to_date=base + timedelta(days=5),
    )

    assert {note.title for note in notes} == {"Old"}


@pytest.mark.asyncio
async def test_get_notes_filters_between_dates(
    dishka_request: AsyncContainer,
    repo_hub: RepositoryHub,
    user: User,
):
    interactor = await dishka_request.get(GetNotesInteractor)
    base = datetime(2024, 1, 1, 12, 0, 0)
    await _create_note_with_created_at(repo_hub, user, "Early", base)
    await _create_note_with_created_at(repo_hub, user, "Middle", base + timedelta(days=5))
    await _create_note_with_created_at(repo_hub, user, "Late", base + timedelta(days=10))

    notes = await interactor.get_notes(
        user.telegram_id,
        from_date=base + timedelta(days=3),
        to_date=base + timedelta(days=7),
    )

    assert {note.title for note in notes} == {"Middle"}
