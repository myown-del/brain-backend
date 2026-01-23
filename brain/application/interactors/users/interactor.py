from uuid import uuid4

from brain.application.abstractions.repositories.users import IUsersRepository
from brain.application.interactors.users.dto import CreateOrUpdateUser
from brain.domain.entities.user import User


class UserInteractor:
    def __init__(
        self,
        users_repo: IUsersRepository,
    ):
        self._users_repo = users_repo

    async def create_or_update_user(self, user_data: CreateOrUpdateUser):
        user_entity = User(
            id=uuid4(),
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        user = await self._users_repo.get_by_telegram_id(user_data.telegram_id)
        if user:
            user_entity.id = user.id
            user_entity.profile_picture_file_id = user.profile_picture_file_id
            await self._users_repo.update(user_entity)
        else:
            await self._users_repo.create(user_entity)
