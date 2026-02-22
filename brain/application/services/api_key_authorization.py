from brain.application.abstractions.repositories.api_keys import IApiKeysRepository
from brain.application.interactors.auth.exceptions import ApiKeyInvalidException
from brain.application.services.user_lookup import UserLookupService
from brain.domain.entities.user import User
from brain.domain.services.api_keys import IApiKeyService


class ApiKeyAuthorizationService:
    def __init__(
        self,
        api_keys_repo: IApiKeysRepository,
        api_key_service: IApiKeyService,
        user_lookup_service: UserLookupService,
    ):
        self._api_keys_repo = api_keys_repo
        self._api_key_service = api_key_service
        self._user_lookup_service = user_lookup_service

    async def authorize(self, api_key: str) -> User:
        key_hash = self._api_key_service.hash_key(api_key)
        key_entity = await self._api_keys_repo.get_by_hash(key_hash)
        if not key_entity:
            raise ApiKeyInvalidException()
        return await self._user_lookup_service.get_user_by_id(key_entity.user_id)
