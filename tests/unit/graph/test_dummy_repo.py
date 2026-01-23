import pytest
from uuid import uuid4
from brain.domain.entities.note import Note
from tests.mocks.notes_graph_repo import DummyNotesGraphRepository


@pytest.mark.asyncio
async def test_dummy_repo_logic():
    repo = DummyNotesGraphRepository()
    user_id = uuid4()
    note_id = uuid4()
    
    note = Note(
        id=note_id,
        user_id=user_id,
        title="Source",
        represents_keyword_id=uuid4(),
    )
    
    # 1. Upsert note
    await repo.upsert_note(note)
    count = await repo.count_notes_by_user_and_title(user_id, "Source")
    assert count == 1
    
    # 2. Sync links (Source -> Target)
    await repo.sync_connections(note, ["Target"])
    
    # 3. Check links
    links = await repo.count_links_between_notes(user_id, "Source", "Target")
    assert links == 1
    
    # 4. Check non-existent user
    links_other = await repo.count_links_between_notes(uuid4(), "Source", "Target")
    assert links_other == 0
    
    # 5. Check persistence across instances (Class vars)
    repo2 = DummyNotesGraphRepository()
    links_2 = await repo2.count_links_between_notes(user_id, "Source", "Target")
    assert links_2 == 1
