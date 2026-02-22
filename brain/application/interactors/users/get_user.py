from uuid import UUID

from brain.application.services.user_lookup import UserLookupService
from brain.domain.entities.user import User


class GetUserInteractor:
    def __init__(self, user_lookup_service: UserLookupService):
        self._user_lookup_service = user_lookup_service

    async def get_user_by_telegram_id(self, telegram_id: int) -> User:
        return await self._user_lookup_service.get_user_by_telegram_id(telegram_id)

    async def get_user_by_id(self, user_id: UUID) -> User:
        return await self._user_lookup_service.get_user_by_id(user_id)
