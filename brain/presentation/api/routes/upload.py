import uuid
from fastapi import APIRouter, UploadFile, File
from dishka.integrations.fastapi import FromDishka, inject
from starlette import status

from brain.infrastructure.s3.client import S3Client
from brain.config.models import S3Config


@inject
async def upload_image(
    s3_client: FromDishka[S3Client],
    s3_config: FromDishka[S3Config],
    file: UploadFile = File(...),
):
    content = await file.read()
    extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    object_name = f"{uuid.uuid4()}.{extension}"

    url = s3_client.upload_file(content, object_name, content_type=file.content_type)
    url = url.replace(s3_config.endpoint_url, s3_config.external_host)
    return {"url": url}


def get_router() -> APIRouter:
    router = APIRouter(prefix="/upload", tags=["Upload"])
    router.add_api_route(
        path="/image",
        endpoint=upload_image,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
    )
    return router
