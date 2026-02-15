from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from brain.domain.entities.s3_file import S3File


class IS3FilesRepository(Protocol):
    @abstractmethod
    async def get_by_id(self, file_id: UUID) -> S3File | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> S3File | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, entity: S3File) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: S3File) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> None:
        raise NotImplementedError
