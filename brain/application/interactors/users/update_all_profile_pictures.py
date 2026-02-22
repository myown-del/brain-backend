from brain.application.abstractions.repositories.users import IUsersRepository
from brain.application.abstractions.services.profile_picture_provider import IProfilePictureProvider
from brain.application.services.user_profile_picture import UserProfilePictureService


class UpdateAllUsersProfilePicturesInteractor:
    def __init__(
        self,
        users_repo: IUsersRepository,
        profile_picture_provider: IProfilePictureProvider,
        user_profile_picture_service: UserProfilePictureService,
    ):
        self._users_repo = users_repo
        self._profile_picture_provider = profile_picture_provider
        self._user_profile_picture_service = user_profile_picture_service

    async def execute(self) -> None:
        users = await self._users_repo.get_all()
        for user in users:
            try:
                result = await self._profile_picture_provider.get_profile_picture_content(user.telegram_id)
                if not result:
                    continue

                await self._user_profile_picture_service.upload_profile_picture(
                    telegram_id=user.telegram_id,
                    image_content=result.content,
                    content_type=result.content_type,
                )
            except Exception:
                continue
