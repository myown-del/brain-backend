from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends
from starlette import status

from brain.config.models import S3Config
from brain.domain.entities.user import User
from brain.presentation.api.dependencies.auth import get_user_from_request
from brain.presentation.api.routes.users.mappers import map_user_to_read_schema
from brain.presentation.api.routes.users.models import ReadUserSchema


@inject
async def get_me(
    s3_config: FromDishka[S3Config],
    user: User = Depends(get_user_from_request),
) -> ReadUserSchema:
    return map_user_to_read_schema(user, s3_config)


def get_router() -> APIRouter:
    router = APIRouter(prefix="/users", tags=["Users"])
    router.add_api_route(
        path="/me",
        endpoint=get_me,
        methods=["GET"],
        response_model=ReadUserSchema,
        summary="Get current user",
        status_code=status.HTTP_200_OK,
    )
    return router
