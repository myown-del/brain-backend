import pytest
from uuid import uuid4
from dishka import AsyncContainer
from brain.application.interactors import CreateNoteInteractor, UpdateNoteInteractor
from brain.application.interactors.notes.dto import CreateNote, UpdateNote
from brain.application.interactors.notes.exceptions import (
    NoteTitleAlreadyExistsException,
    NoteTitleRequiredException,
    NoteNotFoundException,
)
from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub
from brain.domain.services.diffs import get_patches_str


@pytest.mark.asyncio
async def test_note_update_requires_title(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    update_interactor = await dishka_request.get(UpdateNoteInteractor)

    note_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Alpha",
            text="Note",
        ),
    )
    with pytest.raises(NoteTitleRequiredException):
        await update_interactor.update_note(
            UpdateNote(
                note_id=note_id,
                title=None,
                text="Note",
            ),
        )


@pytest.mark.asyncio
async def test_note_duplicate_title_conflict(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    update_interactor = await dishka_request.get(UpdateNoteInteractor)

    await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Omega",
            text="Keyword note",
        ),
    )

    note_id = await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Sigma",
            text="Regular note",
        ),
    )

    with pytest.raises(NoteTitleAlreadyExistsException):
        await update_interactor.update_note(
            UpdateNote(
                note_id=note_id,
                title="Omega",
                text="Regular note",
            ),
        )


@pytest.mark.asyncio
async def test_note_update_renaming(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    update_interactor = await dishka_request.get(UpdateNoteInteractor)
    graph_repo = await dishka_request.get(INotesGraphRepository)

    # Create original
    note_id = await create_interactor.create_note(CreateNote(
        by_user_telegram_id=user.telegram_id,
        title="OldName",
        text="Text",
    ))

    # Rename
    await update_interactor.update_note(UpdateNote(
        note_id=note_id,
        title="NewName",
        text="Text",
    ))

    # Verify PG
    note = await repo_hub.notes.get_by_id(note_id)
    assert note.title == "NewName"

    # Verify Graph (Old node gone/renamed, New node exists)
    old_count = await graph_repo.count_notes_by_user_and_title(user.id, "OldName")
    assert old_count == 0
    new_count = await graph_repo.count_notes_by_user_and_title(user.id, "NewName")
    assert new_count == 1
    
    # Verify Keyword persistence
    kw = await repo_hub.keywords.get_by_id(note.represents_keyword_id)
    assert kw.name == "NewName"


@pytest.mark.asyncio
async def test_note_update_content_links(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    update_interactor = await dishka_request.get(UpdateNoteInteractor)
    graph_repo = await dishka_request.get(INotesGraphRepository)

    note_id = await create_interactor.create_note(CreateNote(
        by_user_telegram_id=user.telegram_id,
        title="Linker",
        text="Refers [[A]]",
    ))

    # Update: remove A, add B
    await update_interactor.update_note(UpdateNote(
        note_id=note_id,
        title="Linker",
        text="Refers [[B]]",
    ))

    # Verify Graph
    count_a = await graph_repo.count_links_between_notes(user.id, "Linker", "A")
    assert count_a == 0
    
    count_b = await graph_repo.count_links_between_notes(user.id, "Linker", "B")
    assert count_b == 1


@pytest.mark.asyncio
async def test_note_update_patch(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    update_interactor = await dishka_request.get(UpdateNoteInteractor)
    
    note_id = await create_interactor.create_note(CreateNote(
        by_user_telegram_id=user.telegram_id,
        title="Patcher",
        text="Hello world",
    ))

    patch_str = get_patches_str("Hello world", "Hello patched")
    
    updated_note = await update_interactor.update_note(UpdateNote(
        note_id=note_id,
        title="Patcher",
        text=None,
        patch=patch_str,
    ))
    
    assert updated_note.text == "Hello patched"
    
    db_note = await repo_hub.notes.get_by_id(note_id)
    assert db_note.text == "Hello patched"


@pytest.mark.asyncio
async def test_note_update_keyword_gc(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    update_interactor = await dishka_request.get(UpdateNoteInteractor)

    # 1. Create note linking to "Temporary"
    note_id = await create_interactor.create_note(CreateNote(
        by_user_telegram_id=user.telegram_id,
        title="Holder",
        text="Links [[Temporary]]",
    ))
    
    # Verify keyword exists
    kw = await repo_hub.keywords.get_by_user_and_name(user.id, "Temporary")
    assert kw is not None

    # 2. Update note to remove link
    await update_interactor.update_note(UpdateNote(
        note_id=note_id,
        title="Holder",
        text="Cleaning up links",
    ))
    
    # 3. Verify keyword "Temporary" is gone (Garbage Collected)
    kw_after = await repo_hub.keywords.get_by_user_and_name(user.id, "Temporary")
    assert kw_after is None


@pytest.mark.asyncio
async def test_note_update_not_found(
    dishka_request: AsyncContainer,
):
    update_interactor = await dishka_request.get(UpdateNoteInteractor)
    
    with pytest.raises(NoteNotFoundException):
        await update_interactor.update_note(UpdateNote(
            note_id=uuid4(),
            title="Ghost",
            text="Boo",
        ))


@pytest.mark.asyncio
async def test_note_update_removes_wikilink_connection(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    update_interactor = await dishka_request.get(UpdateNoteInteractor)
    graph_repo = await dishka_request.get(INotesGraphRepository)

    # 1. Create a note with a wikilink
    note_id = await create_interactor.create_note(CreateNote(
        by_user_telegram_id=user.telegram_id,
        title="Source",
        text="This refers to [[Target]]",
    ))

    # Verify link exists initially
    initial_count = await graph_repo.count_links_between_notes(user.id, "Source", "Target")
    assert initial_count == 1

    # 2. Update the note to remove the wikilink
    await update_interactor.update_note(UpdateNote(
        note_id=note_id,
        title="Source",
        text="No links here anymore",
    ))

    # 3. Verify link is gone
    final_count = await graph_repo.count_links_between_notes(user.id, "Source", "Target")
    assert final_count == 0
