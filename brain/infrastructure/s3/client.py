import boto3
from botocore.config import Config as BotoConfig

from brain.config.models import S3Config


class S3Client:
    def __init__(self, config: S3Config):
        self.config = config
        self.client = boto3.client(
            "s3",
            endpoint_url=self.config.endpoint_url,
            aws_access_key_id=self.config.access_key_id,
            aws_secret_access_key=self.config.secret_access_key,
            region_name=self.config.region_name,
            config=BotoConfig(signature_version="s3v4"),
        )
        self.bucket = self.config.bucket_name

    def upload_file(self, file_content: bytes, object_name: str, content_type: str = None) -> str:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.put_object(
            Bucket=self.bucket,
            Key=object_name,
            Body=file_content,
            **extra_args,
        )

        return f"{self.config.endpoint_url}/{self.bucket}/{object_name}"
