from brain.domain.entities.s3_file import S3File
from brain.infrastructure.db.mappers import normalize_datetime
from brain.infrastructure.db.models.s3 import S3FileDB


def map_s3_file_to_dm(file_db: S3FileDB) -> S3File:
    return S3File(
        id=file_db.id,
        object_name=file_db.object_name,
        content_type=file_db.content_type,
        created_at=normalize_datetime(file_db.created_at),
        updated_at=normalize_datetime(file_db.updated_at),
    )


def map_s3_file_to_db(file_dm: S3File) -> S3FileDB:
    return S3FileDB(
        id=file_dm.id,
        object_name=file_dm.object_name,
        content_type=file_dm.content_type,
        created_at=normalize_datetime(file_dm.created_at),
        updated_at=normalize_datetime(file_dm.updated_at),
    )

