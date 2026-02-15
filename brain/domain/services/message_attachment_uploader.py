from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class IMessageAttachmentUploader(ABC):
    @abstractmethod
    def can_handle(self, message: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def upload(
        self,
        message: Any,
        upload_file_interactor: Any,
    ) -> UUID | None:
        raise NotImplementedError
