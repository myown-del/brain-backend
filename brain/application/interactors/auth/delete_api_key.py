from uuid import UUID

from brain.application.abstractions.repositories.api_keys import IApiKeysRepository
from brain.application.abstractions.uow import UnitOfWorkFactory
from brain.application.interactors.auth.exceptions import ApiKeyNotFoundException


class DeleteApiKeyInteractor:
    def __init__(
        self,
        api_keys_repo: IApiKeysRepository,
        uow_factory: UnitOfWorkFactory,
    ):
        self._api_keys_repo = api_keys_repo
        self._uow_factory = uow_factory

    async def delete_api_key(self, api_key_id: UUID, user_id: UUID) -> None:
        async with self._uow_factory() as uow:
            deleted = await self._api_keys_repo.delete_by_id_and_user_id(
                api_key_id=api_key_id,
                user_id=user_id,
            )
            if not deleted:
                raise ApiKeyNotFoundException()
            await uow.commit()
