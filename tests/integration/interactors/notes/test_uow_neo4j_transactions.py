from unittest.mock import AsyncMock

import pytest
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.interactors import CreateNoteInteractor
from brain.application.interactors.notes.dto import CreateNote
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub


@pytest.mark.asyncio
async def test_create_note_rolls_back_both_stores_on_error_before_commit(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    graph_repo = await dishka_request.get(INotesGraphRepository)

    failing_sync = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(
        create_interactor._note_creation_service._keyword_sync_service,  # type: ignore[attr-defined]
        "sync",
        failing_sync,
    )

    with pytest.raises(RuntimeError, match="boom"):
        await create_interactor.create_note(
            CreateNote(
                by_user_telegram_id=user.telegram_id,
                title="RollbackBothStores",
                text="content",
            ),
        )

    note = await repo_hub.notes.get_by_title(
        user_id=user.id,
        title="RollbackBothStores",
        exact_match=True,
    )
    assert note is None

    graph_count = await graph_repo.count_notes_by_user_and_title(
        user_id=user.id,
        title="RollbackBothStores",
    )
    assert graph_count == 0


@pytest.mark.asyncio
async def test_commit_persists_sql_then_neo4j(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
) -> None:
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    graph_repo = await dishka_request.get(INotesGraphRepository)

    note_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="CommitBothStores",
            text="content",
        ),
    )

    note = await repo_hub.notes.get_by_id(note_id)
    assert note is not None
    assert note.title == "CommitBothStores"

    graph_count = await graph_repo.count_notes_by_user_and_title(
        user_id=user.id,
        title="CommitBothStores",
    )
    assert graph_count == 1


@pytest.mark.asyncio
async def test_uow_exit_without_commit_and_without_exception_does_not_autorollback(
    dishka_request: AsyncContainer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uow_factory = await dishka_request.get(UnitOfWorkFactory)
    sql_session = await dishka_request.get(AsyncSession)

    rollback_spy = AsyncMock(wraps=sql_session.rollback)
    monkeypatch.setattr(sql_session, "rollback", rollback_spy)

    async with uow_factory():
        pass

    rollback_spy.assert_not_awaited()
