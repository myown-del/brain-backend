from brain.config.models import S3Config

from brain.domain.entities.user import User
from brain.presentation.api.routes.users.models import ReadS3FileSchema
from brain.presentation.api.routes.users.models import ReadUserSchema


def _build_s3_public_url(*, s3_config: S3Config, object_name: str) -> str:
    base = (s3_config.external_host or "").rstrip("/")
    bucket = (s3_config.bucket_name or "").strip("/")
    key = object_name.lstrip("/")
    return f"{base}/{bucket}/{key}"


def map_user_to_read_schema(user: User, s3_config: S3Config) -> ReadUserSchema:
    profile_picture: ReadS3FileSchema | None = None
    if user.profile_picture is not None:
        profile_picture = ReadS3FileSchema(
            id=user.profile_picture.id,
            object_name=user.profile_picture.object_name,
            url=_build_s3_public_url(
                s3_config=s3_config,
                object_name=user.profile_picture.object_name,
            ),
            content_type=user.profile_picture.content_type,
            created_at=user.profile_picture.created_at,
            updated_at=user.profile_picture.updated_at,
        )

    return ReadUserSchema(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        profile_picture=profile_picture,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
