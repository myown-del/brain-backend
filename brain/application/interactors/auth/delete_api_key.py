from uuid import UUID

from brain.application.abstractions.repositories.api_keys import IApiKeysRepository
from brain.application.interactors.auth.exceptions import ApiKeyNotFoundException


class DeleteApiKeyInteractor:
    def __init__(
        self,
        api_keys_repo: IApiKeysRepository,
    ):
        self._api_keys_repo = api_keys_repo

    async def delete_api_key(self, api_key_id: UUID, user_id: UUID) -> None:
        deleted = await self._api_keys_repo.delete_by_id_and_user_id(
            api_key_id=api_key_id,
            user_id=user_id,
        )
        if not deleted:
            raise ApiKeyNotFoundException()
