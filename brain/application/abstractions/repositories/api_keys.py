from uuid import UUID

from abc import abstractmethod
from typing import Protocol

from brain.domain.entities.api_key import ApiKey


class IApiKeysRepository(Protocol):
    @abstractmethod
    async def create(self, entity: ApiKey) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        raise NotImplementedError

    @abstractmethod
    async def get_all_by_user_id(self, user_id: UUID) -> list[ApiKey]:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id_and_user_id(self, api_key_id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError
