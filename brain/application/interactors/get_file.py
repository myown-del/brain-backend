from uuid import UUID

from brain.application.abstractions.repositories.s3_files import IS3FilesRepository
from brain.application.interactors.file_dto import ReadFileOutput
from brain.config.models import S3Config
from brain.domain.services.media import build_public_file_url


class FileNotFoundException(Exception):
    pass


class GetFileInteractor:
    def __init__(
        self,
        s3_files_repo: IS3FilesRepository,
        s3_config: S3Config,
    ):
        self._s3_files_repo = s3_files_repo
        self._s3_config = s3_config

    async def get_file_by_id(self, file_id: UUID) -> ReadFileOutput:
        file = await self._s3_files_repo.get_by_id(file_id=file_id)
        if not file:
            raise FileNotFoundException()
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
