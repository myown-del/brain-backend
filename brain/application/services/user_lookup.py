from uuid import UUID

from brain.application.abstractions.repositories.users import IUsersRepository
from brain.application.interactors.users.exceptions import UserNotFoundException
from brain.domain.entities.user import User


class UserLookupService:
    def __init__(self, users_repo: IUsersRepository):
        self._users_repo = users_repo

    async def get_user_by_telegram_id(self, telegram_id: int) -> User:
        user = await self._users_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise UserNotFoundException()
        return user

    async def get_user_by_id(self, user_id: UUID) -> User:
        user = await self._users_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        return user
