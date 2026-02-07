from uuid import UUID

from brain.application.abstractions.repositories.api_keys import IApiKeysRepository
from brain.domain.entities.api_key import ApiKey


class GetApiKeysInteractor:
    def __init__(
        self,
        api_keys_repo: IApiKeysRepository,
    ):
        self._api_keys_repo = api_keys_repo

    async def get_api_keys(self, user_id: UUID) -> list[ApiKey]:
        return await self._api_keys_repo.get_all_by_user_id(user_id)
