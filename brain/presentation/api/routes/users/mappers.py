from brain.domain.entities.user import User
from brain.config.models import S3Config
from brain.domain.services.media import build_public_file_url
from brain.presentation.api.routes.users.models import ReadS3FileSchema
from brain.presentation.api.routes.users.models import ReadUserSchema


def map_user_to_read_schema(user: User, s3_config: S3Config) -> ReadUserSchema:
    profile_picture: ReadS3FileSchema | None = None
    if user.profile_picture is not None:
        profile_picture = ReadS3FileSchema(
            id=user.profile_picture.id,
            name=user.profile_picture.name,
            path=user.profile_picture.path,
            url=build_public_file_url(
                external_host=s3_config.external_host,
                file_path=user.profile_picture.path,
            ),
            content_type=user.profile_picture.content_type,
            created_at=user.profile_picture.created_at,
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
