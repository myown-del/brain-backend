from brain.domain.entities.note import Note
from brain.infrastructure.db.mappers import normalize_datetime
from brain.infrastructure.db.models.note import NoteDB
from brain.domain.value_objects import LinkInterval


def map_note_to_dm(note: NoteDB) -> Note:
    return Note(
        id=note.id,
        user_id=note.user_id,
        title=note.title,
        text=note.text,
        represents_keyword_id=note.represents_keyword_id,
        is_pinned=note.is_pinned,
        created_at=normalize_datetime(note.created_at),
        updated_at=normalize_datetime(note.updated_at),
        link_intervals=[LinkInterval(interval[0], interval[1]) for interval in note.link_intervals],
    )


def map_note_to_db(note: Note) -> NoteDB:
    return NoteDB(
        id=note.id,
        user_id=note.user_id,
        title=note.title,
        text=note.text,
        represents_keyword_id=note.represents_keyword_id,
        is_pinned=note.is_pinned,
        created_at=normalize_datetime(note.created_at),
        updated_at=normalize_datetime(note.updated_at),
        link_intervals=[[interval.start, interval.end] for interval in note.link_intervals],
    )

