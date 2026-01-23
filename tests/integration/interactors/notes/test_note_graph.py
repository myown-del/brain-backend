import pytest

from brain.application.abstractions.repositories.notes_graph import (
    INotesGraphRepository,
)
from brain.application.interactors.notes.dto import CreateNote
from brain.application.interactors import CreateNoteInteractor
from brain.domain.entities.user import User


@pytest.mark.asyncio
async def test_note_graph_links_to_notes_by_title(dishka_request, user: User):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    notes_graph_repo = await dishka_request.get(INotesGraphRepository)

    child_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Child",
            text="leaf",
        ),
    )
    await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Root",
            text="see [[Child]] and [[Child|alias]]",
        ),
    )

    count = await notes_graph_repo.count_notes_by_user_and_title(
        user_id=user.id,
        title="Root",
    )
    assert count == 1

    link_count = await notes_graph_repo.count_links_between_notes(
        user_id=user.id,
        from_title="Root",
        to_title="Child",
    )
    assert link_count == 1
