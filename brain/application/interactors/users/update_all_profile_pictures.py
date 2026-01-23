from brain.application.abstractions.repositories.users import IUsersRepository
from brain.application.abstractions.services.profile_picture_provider import (
    IProfilePictureProvider,
)
from brain.application.interactors.users.upload_profile_picture import (
    UploadUserProfilePictureInteractor,
)


class UpdateAllUsersProfilePicturesInteractor:
    def __init__(
        self,
        users_repo: IUsersRepository,
        profile_picture_provider: IProfilePictureProvider,
        upload_interactor: UploadUserProfilePictureInteractor,
    ):
        self._users_repo = users_repo
        self._profile_picture_provider = profile_picture_provider
        self._upload_interactor = upload_interactor

    async def execute(self) -> None:
        users = await self._users_repo.get_all()
        for user in users:
            try:
                result = await self._profile_picture_provider.get_profile_picture_content(user.telegram_id)
                if not result:
                    continue

                await self._upload_interactor.upload_profile_picture(
                    telegram_id=user.telegram_id,
                    image_content=result.content,
                    content_type=result.content_type,
                )
            except Exception:
                # Log error or continue to next user to avoid stopping the whole process
                # Ideally we should inject a logger here
                continue
