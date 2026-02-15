from brain.application.abstractions.storage.files import IFileStorage
from brain.config.models import S3Config
from brain.infrastructure.s3.client import S3Client


class S3FileStorage(IFileStorage):
    def __init__(self, s3_client: S3Client, s3_config: S3Config):
        self._s3_client = s3_client
        self._s3_config = s3_config

    def upload(
        self,
        content: bytes,
        object_name: str,
        content_type: str | None = None,
    ) -> str:
        url = self._s3_client.upload_file(
            file_content=content,
            object_name=object_name,
            content_type=content_type,
        )
        return url.replace(self._s3_config.endpoint_url, self._s3_config.external_host)
