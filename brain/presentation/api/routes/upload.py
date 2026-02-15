from fastapi import APIRouter, UploadFile, File
from dishka.integrations.fastapi import FromDishka, inject
from starlette import status

from brain.application.interactors.upload_file import UploadFileInteractor
from brain.presentation.api.routes.upload_models import ReadUploadedFileSchema


@inject
async def upload_file(
    interactor: FromDishka[UploadFileInteractor],
    file: UploadFile = File(...),
) -> ReadUploadedFileSchema:
    content = await file.read()
    url = await interactor.upload_file(
        filename=file.filename,
        content=content,
        content_type=file.content_type,
    )
    return ReadUploadedFileSchema(url=url)


def get_router() -> APIRouter:
    router = APIRouter(prefix="/upload", tags=["Upload"])
    router.add_api_route(
        path="/file",
        endpoint=upload_file,
        methods=["POST"],
        response_model=ReadUploadedFileSchema,
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/image",
        endpoint=upload_file,
        methods=["POST"],
        response_model=ReadUploadedFileSchema,
        status_code=status.HTTP_200_OK,
        deprecated=True,
    )
    return router
