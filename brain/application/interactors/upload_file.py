from uuid import uuid4

from brain.application.abstractions.repositories.s3_files import IS3FilesRepository
from brain.application.abstractions.storage.files import IFileStorage
from brain.application.interactors.file_dto import ReadFileOutput
from brain.config.models import S3Config
from brain.domain.entities.s3_file import S3File
from brain.domain.services.media import build_public_file_url, get_file_extension


class UploadFileInteractor:
    def __init__(
        self,
        file_storage: IFileStorage,
        s3_files_repo: IS3FilesRepository,
        s3_config: S3Config,
    ):
        self._file_storage = file_storage
        self._s3_files_repo = s3_files_repo
        self._s3_config = s3_config

    async def upload_file(
        self,
        filename: str | None,
        content: bytes,
        content_type: str | None = None,
    ) -> ReadFileOutput:
        extension = get_file_extension(filename)
        name = f"{uuid4()}.{extension}"
        object_name = name
        normalized_content_type = content_type or "application/octet-stream"
        self._file_storage.upload(
            content=content,
            object_name=object_name,
            content_type=normalized_content_type,
        )
        file = S3File(
            id=uuid4(),
            name=name,
            path=object_name,
            content_type=normalized_content_type,
        )
        await self._s3_files_repo.create(entity=file)
        return ReadFileOutput(
            id=file.id,
            name=file.name,
            path=file.path,
            content_type=file.content_type,
            created_at=file.created_at,
            url=build_public_file_url(
                external_host=self._s3_config.external_host,
                file_path=file.path,
            ),
        )
