from brain.application.services.user_profile_picture import UserProfilePictureService
from brain.domain.entities.s3_file import S3File


class UploadUserProfilePictureInteractor:
    def __init__(self, user_profile_picture_service: UserProfilePictureService):
        self._user_profile_picture_service = user_profile_picture_service

    async def upload_profile_picture(
        self,
        telegram_id: int,
        image_content: bytes,
        content_type: str | None = None,
    ) -> S3File:
        return await self._user_profile_picture_service.upload_profile_picture(
            telegram_id=telegram_id,
            image_content=image_content,
            content_type=content_type,
        )
