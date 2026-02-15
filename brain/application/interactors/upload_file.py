from uuid import uuid4

from brain.application.abstractions.storage.files import IFileStorage
from brain.domain.services.media import get_file_extension


class UploadFileInteractor:
    def __init__(self, file_storage: IFileStorage):
        self._file_storage = file_storage

    async def upload_file(
        self,
        filename: str | None,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        extension = get_file_extension(filename)
        object_name = f"{uuid4()}.{extension}"
        return self._file_storage.upload(
            content=content,
            object_name=object_name,
            content_type=content_type,
        )
