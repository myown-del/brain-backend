from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette import status

from brain.application.interactors.get_file import GetFileInteractor, FileNotFoundException
from brain.application.interactors.upload_file import UploadFileInteractor
from brain.presentation.api.routes.upload_models import ReadUploadedFileSchema


@inject
async def upload_file(
    interactor: FromDishka[UploadFileInteractor],
    file: UploadFile = File(...),
) -> ReadUploadedFileSchema:
    content = await file.read()
    uploaded_file = await interactor.upload_file(
        filename=file.filename,
        content=content,
        content_type=file.content_type,
    )
    return ReadUploadedFileSchema(
        id=uploaded_file.id,
        name=uploaded_file.name,
        path=uploaded_file.path,
        url=uploaded_file.url,
        content_type=uploaded_file.content_type,
        created_at=uploaded_file.created_at,
    )


@inject
async def get_file(
    file_id: UUID,
    interactor: FromDishka[GetFileInteractor],
) -> ReadUploadedFileSchema:
    try:
        file = await interactor.get_file_by_id(file_id=file_id)
    except FileNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return ReadUploadedFileSchema(
        id=file.id,
        name=file.name,
        path=file.path,
        url=file.url,
        content_type=file.content_type,
        created_at=file.created_at,
    )


def get_router() -> APIRouter:
    router = APIRouter(prefix="/file", tags=["Upload"])
    router.add_api_route(
        path="/upload",
        endpoint=upload_file,
        methods=["POST"],
        response_model=ReadUploadedFileSchema,
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/{file_id}",
        endpoint=get_file,
        methods=["GET"],
        response_model=ReadUploadedFileSchema,
        status_code=status.HTTP_200_OK,
    )
    return router
