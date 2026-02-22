import pytest
from unittest.mock import AsyncMock, MagicMock, ANY
from uuid import uuid4

from brain.application.abstractions.uow import IUnitOfWork
from brain.application.interactors.notes.update_note import UpdateNoteInteractor
from brain.application.interactors.notes.dto import UpdateNote
from brain.application.services.note_crud import NoteUpdateService
from brain.domain.entities.note import Note
from brain.domain.value_objects import LinkInterval
from brain.application.abstractions.repositories.notes import INotesRepository
from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.application.abstractions.repositories.keywords import IKeywordsRepository
from brain.application.services.keyword_notes import KeywordNoteService
from brain.application.services.note_titles import NoteTitleService
from brain.application.services.note_keyword_sync import NoteKeywordSyncService


class FakeUnitOfWork(IUnitOfWork):
    def __init__(self):
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.flush = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.fixture
def notes_repo():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def notes_graph_repo():
    repo = AsyncMock()
    repo.upsert_note = AsyncMock()
    return repo


@pytest.fixture
def keywords_repo():
    repo = AsyncMock()
    repo.delete_unused_keywords = AsyncMock()
    return repo


@pytest.fixture
def keyword_note_service():
    service = AsyncMock()
    service.ensure_keyword_for_title = AsyncMock(return_value=uuid4())
    return service


@pytest.fixture
def note_title_service():
    service = AsyncMock()
    service.ensure_update_title = AsyncMock(side_effect=lambda user_id, title, exclude_note_id: title)
    return service


@pytest.fixture
def keyword_sync_service():
    service = AsyncMock()
    service.sync = AsyncMock()
    return service


@pytest.fixture
def interactor(
    notes_repo, notes_graph_repo, keywords_repo, keyword_note_service, note_title_service, keyword_sync_service
):
    note_update_service = NoteUpdateService(
        notes_repo=notes_repo,
        notes_graph_repo=notes_graph_repo,
        keywords_repo=keywords_repo,
        keyword_note_service=keyword_note_service,
        note_title_service=note_title_service,
        keyword_sync_service=keyword_sync_service,
    )
    uow = FakeUnitOfWork()
    interactor_ = UpdateNoteInteractor(
        note_update_service=note_update_service,
        uow_factory=lambda: uow,
    )
    interactor_._test_uow = uow  # type: ignore[attr-defined]
    return interactor_


@pytest.mark.asyncio
async def test_update_note_with_text_updates_full_content(interactor, notes_repo, keyword_sync_service):
    note_id = uuid4()
    original_text = "Original"
    new_text = "New content"

    existing_note = Note(
        id=note_id,
        user_id=uuid4(),
        title="Title",
        text=original_text,
        represents_keyword_id=uuid4(),
        link_intervals=[],
    )
    notes_repo.get_by_id.return_value = existing_note

    dto = UpdateNote(note_id=note_id, title="Title", text=new_text, patch=None)

    updated_note = await interactor.update_note(dto)

    assert updated_note.text == new_text
    keyword_sync_service.sync.assert_called_once()
    assert len(updated_note.link_intervals) == 0
    interactor._test_uow.commit.assert_awaited_once()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_update_note_with_patch_applies_correctly(interactor, notes_repo, keyword_sync_service):
    # original: "Hello world"
    # patch: change "world" to "Friends"
    # new: "Hello Friends"

    note_id = uuid4()
    original_text = "Hello world"
    # Patch generated via diff-match-patch for "Hello world" -> "Hello Friends"
    # explicit patch string requires proper format.
    # using dmp to generate it helper?
    import diff_match_patch as dmp_module

    dmp = dmp_module.diff_match_patch()
    patches = dmp.patch_make(original_text, "Hello Friends")
    patch_text = dmp.patch_toText(patches)

    existing_note = Note(
        id=note_id,
        user_id=uuid4(),
        title="Title",
        text=original_text,
        represents_keyword_id=uuid4(),
        link_intervals=[],
    )
    notes_repo.get_by_id.return_value = existing_note

    dto = UpdateNote(note_id=note_id, title="Title", text=None, patch=patch_text)

    updated_note = await interactor.update_note(dto)

    assert updated_note.text == "Hello Friends"
    keyword_sync_service.sync.assert_called_once()  # Called because no old intervals to optimize against? Or just because default is true.
    # note.link_intervals was empty, so diff check happened between "" and "", or skipped?
    # Logic: if note.link_intervals and note_data.patch:
    # Here link_intervals is empty. So optimization block SKIPPED.
    # Should sync graph = True.


@pytest.mark.asyncio
async def test_update_note_optimizes_sync_when_links_untouched(interactor, notes_repo, keyword_sync_service):
    # original: "Hello [[Link]] world"
    # interval for [[Link]]: starts at 6. Len 8? "[[Link]]".
    # text: "Hello [[Link]] world"
    #        01234567890123456789
    #        H e l l o   [ [ L i n k ] ]   w o r l d
    # Link starts at 6. Ends at 14.

    note_id = uuid4()
    original_text = "Hello [[Link]] world"
    existing_note = Note(
        id=note_id,
        user_id=uuid4(),
        title="Title",
        text=original_text,
        represents_keyword_id=uuid4(),
        link_intervals=[LinkInterval(6, 14)],  # [[Link]]
    )
    notes_repo.get_by_id.return_value = existing_note

    # Change "world" to "Environment". "[[Link]]" is untouched.
    # New text: "Hello [[Link]] Environment"
    import diff_match_patch as dmp_module

    dmp = dmp_module.diff_match_patch()
    patches = dmp.patch_make(original_text, "Hello [[Link]] Environment")
    patch_text = dmp.patch_toText(patches)

    dto = UpdateNote(note_id=note_id, title="Title", text=None, patch=patch_text)

    updated_note = await interactor.update_note(dto)

    assert updated_note.text == "Hello [[Link]] Environment"
    # Optimization should trigger: sync NOT called
    keyword_sync_service.sync.assert_not_called()

    # Intervals should be updated (re-parsed)
    # Positions might stay same if change is AFTER link.
    assert updated_note.link_intervals == [LinkInterval(6, 14)]


@pytest.mark.asyncio
async def test_update_note_syncs_when_link_modified(interactor, notes_repo, keyword_sync_service):
    # original: "Hello [[Link]] world"
    note_id = uuid4()
    original_text = "Hello [[Link]] world"
    existing_note = Note(
        id=note_id,
        user_id=uuid4(),
        title="Title",
        text=original_text,
        represents_keyword_id=uuid4(),
        link_intervals=[LinkInterval(6, 14)],
    )
    notes_repo.get_by_id.return_value = existing_note

    # Change "[[Link]]" to "[[Zelda]]"
    import diff_match_patch as dmp_module

    dmp = dmp_module.diff_match_patch()
    patches = dmp.patch_make(original_text, "Hello [[Zelda]] world")
    patch_text = dmp.patch_toText(patches)

    dto = UpdateNote(note_id=note_id, title="Title", text=None, patch=patch_text)

    updated_note = await interactor.update_note(dto)

    assert updated_note.text == "Hello [[Zelda]] world"
    # Optimization should FAIL -> Sync CALLED
    keyword_sync_service.sync.assert_called_once()

    # New interval length likely different
    # [[Zelda]] len 9.
    assert updated_note.link_intervals == [LinkInterval(6, 15)]


@pytest.mark.asyncio
async def test_update_note_syncs_when_new_link_added(interactor, notes_repo, keyword_sync_service):
    # original: "Hello world"
    note_id = uuid4()
    original_text = "Hello world"
    existing_note = Note(
        id=note_id,
        user_id=uuid4(),
        title="Title",
        text=original_text,
        represents_keyword_id=uuid4(),
        link_intervals=[],  # Empty initially, so we need to force optimization check logic?
        # Logic: if note.link_intervals and note_data.patch:
        # If intervals are empty, logic skips!
        # So if I add a link to a note with NO links, it defaults to Sync = True.
        # Which is CORRECT. We must sync.
    )
    # To test "Has New Syntax" check, we need existing links so optimization block is entered.
    original_text = "Hello [[Old]] world"
    existing_note = Note(
        id=note_id,
        user_id=uuid4(),
        title="Title",
        text=original_text,
        represents_keyword_id=uuid4(),
        link_intervals=[LinkInterval(6, 13)],  # [[Old]] len 7
    )
    notes_repo.get_by_id.return_value = existing_note

    # Add new link: "Hello [[Old]] world [[New]]"
    import diff_match_patch as dmp_module

    dmp = dmp_module.diff_match_patch()
    patches = dmp.patch_make(original_text, "Hello [[Old]] world [[New]]")
    patch_text = dmp.patch_toText(patches)

    dto = UpdateNote(note_id=note_id, title="Title", text=None, patch=patch_text)

    await interactor.update_note(dto)

    # Sync MUST be called because of new brackets in patch
    keyword_sync_service.sync.assert_called_once()
