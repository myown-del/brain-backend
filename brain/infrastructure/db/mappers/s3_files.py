from brain.domain.entities.s3_file import S3File
from brain.domain.time import utc_now
from brain.infrastructure.db.mappers import normalize_datetime
from brain.infrastructure.db.models.s3 import S3FileDB


def map_s3_file_to_dm(file_db: S3FileDB) -> S3File:
    return S3File(
        id=file_db.id,
        name=file_db.name,
        path=file_db.path,
        content_type=file_db.content_type,
        created_at=normalize_datetime(file_db.created_at),
    )


def map_s3_file_to_db(file_dm: S3File) -> S3FileDB:
    return S3FileDB(
        id=file_dm.id,
        name=file_dm.name,
        path=file_dm.path,
        content_type=file_dm.content_type,
        created_at=normalize_datetime(file_dm.created_at) or utc_now(),
    )

