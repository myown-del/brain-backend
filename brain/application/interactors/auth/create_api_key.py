from datetime import datetime
from uuid import UUID, uuid4

from brain.application.abstractions.repositories.api_keys import IApiKeysRepository
from brain.application.interactors.auth.dto import CreatedApiKey
from brain.domain.entities.api_key import ApiKey
from brain.domain.services.api_keys import IApiKeyService


class CreateApiKeyInteractor:
    def __init__(
        self,
        api_keys_repo: IApiKeysRepository,
        api_key_service: IApiKeyService,
    ):
        self._api_keys_repo = api_keys_repo
        self._api_key_service = api_key_service

    async def create_api_key(self, user_id: UUID, name: str) -> CreatedApiKey:
        generated_key = self._api_key_service.generate_key()
        api_key = ApiKey(
            id=uuid4(),
            user_id=user_id,
            name=name,
            key_hash=self._api_key_service.hash_key(generated_key),
            created_at=datetime.utcnow(),
        )
        await self._api_keys_repo.create(api_key)
        return CreatedApiKey(
            id=api_key.id,
            name=api_key.name,
            key=generated_key,
            created_at=api_key.created_at,
        )
