from brain.domain.entities.draft import Draft
from brain.infrastructure.db.mappers.s3_files import map_s3_file_to_dm
from brain.infrastructure.db.mappers import normalize_datetime
from brain.infrastructure.db.models.draft import DraftDB


def map_draft_to_dm(draft: DraftDB) -> Draft:
    hashtags = [hashtag.text for hashtag in draft.hashtags if hashtag.text]
    hashtags.sort()
    return Draft(
        id=draft.id,
        user_id=draft.user_id,
        text=draft.text,
        file_id=draft.file_id,
        file=map_s3_file_to_dm(draft.file) if draft.file else None,
        hashtags=hashtags,
        created_at=normalize_datetime(draft.created_at),
        updated_at=normalize_datetime(draft.updated_at),
    )


def map_draft_to_db(draft: Draft) -> DraftDB:
    return DraftDB(
        id=draft.id,
        user_id=draft.user_id,
        text=draft.text,
        file_id=draft.file_id,
        created_at=normalize_datetime(draft.created_at),
        updated_at=normalize_datetime(draft.updated_at),
    )

