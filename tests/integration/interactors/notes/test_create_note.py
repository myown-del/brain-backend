import pytest
from dishka import AsyncContainer
from brain.application.interactors import CreateNoteInteractor
from brain.application.interactors.notes.dto import CreateNote
from brain.application.interactors.notes.exceptions import NoteTitleAlreadyExistsException
from brain.application.interactors.users.exceptions import UserNotFoundException
from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.domain.entities.user import User
from brain.infrastructure.db.repositories.hub import RepositoryHub


@pytest.mark.asyncio
async def test_note_creation(dishka_request: AsyncContainer, user: User, repo_hub: RepositoryHub):
    create_interactor = await dishka_request.get(CreateNoteInteractor)

    data = CreateNote(
        by_user_telegram_id=user.telegram_id,
        title="Note title",
        text="Some note text",
    )
    note_id = await create_interactor.create_note(data)

    note = await repo_hub.notes.get_by_id(note_id)
    assert note is not None
    assert note.user_id == user.id
    assert note.title == data.title
    assert note.text == data.text
    assert note.represents_keyword_id is not None


@pytest.mark.asyncio
async def test_note_autogenerates_title_when_missing(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)

    data = CreateNote(
        by_user_telegram_id=user.telegram_id,
        title=None,
        text="Some note text",
    )
    note_id = await create_interactor.create_note(data)
    note = await repo_hub.notes.get_by_id(note_id)
    assert note is not None
    assert note.title.startswith("Untitled ")
    assert note.represents_keyword_id is not None


@pytest.mark.asyncio
async def test_note_unique_by_title(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)

    await create_interactor.create_note(
        CreateNote(
            by_user_telegram_id=user.telegram_id,
            title="Keyword",
            text="First",
        ),
    )
    with pytest.raises(NoteTitleAlreadyExistsException):
        await create_interactor.create_note(
            CreateNote(
                by_user_telegram_id=user.telegram_id,
                title="Keyword",
                text="Second",
            ),
        )

    notes = await repo_hub.notes.get_by_user_telegram_id(user.telegram_id)
    assert [note.title for note in notes].count("Keyword") == 1


@pytest.mark.asyncio
async def test_note_creation_by_nonexistent_user(dishka_request: AsyncContainer):
    create_interactor = await dishka_request.get(CreateNoteInteractor)

    data = CreateNote(
        by_user_telegram_id=-1,
        title=None,
        text="Some note text",
    )
    with pytest.raises(UserNotFoundException):
        await create_interactor.create_note(data)


@pytest.mark.asyncio
async def test_note_creation_with_wikilinks(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    graph_repo = await dishka_request.get(INotesGraphRepository)

    # Note references "Target"
    data = CreateNote(
        by_user_telegram_id=user.telegram_id,
        title="Source",
        text="Links to [[Target]].",
    )
    note_id = await create_interactor.create_note(data)

    # Verify PG State
    note = await repo_hub.notes.get_by_id(note_id)
    assert note.title == "Source"
    
    # Verify Target Keyword Created
    target_kw = await repo_hub.keywords.get_by_user_and_name(user.id, "Target")
    assert target_kw is not None
    
    # Verify Graph State
    links_count = await graph_repo.count_links_between_notes(user.id, "Source", "Target")
    assert links_count == 1
    
    # Verify nodes count
    source_count = await graph_repo.count_notes_by_user_and_title(user.id, "Source")
    assert source_count == 1
    target_count = await graph_repo.count_notes_by_user_and_title(user.id, "Target")
    assert target_count == 1


@pytest.mark.asyncio
async def test_note_creation_auto_title_with_links(
    dishka_request: AsyncContainer,
    user: User,
    repo_hub: RepositoryHub,
):
    create_interactor = await dishka_request.get(CreateNoteInteractor)
    graph_repo = await dishka_request.get(INotesGraphRepository)

    data = CreateNote(
        by_user_telegram_id=user.telegram_id,
        title=None,
        text="Content with [[Linked]].",
    )
    note_id = await create_interactor.create_note(data)
    note = await repo_hub.notes.get_by_id(note_id)
    
    # Verify link established using generated title
    links_count = await graph_repo.count_links_between_notes(user.id, note.title, "Linked")
    assert links_count == 1
