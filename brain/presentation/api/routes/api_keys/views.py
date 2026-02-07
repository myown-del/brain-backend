from dataclasses import asdict
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, Header, status

from brain.application.interactors.auth.authorize_api_key import AuthorizeApiKeyInteractor
from brain.application.interactors.auth.create_api_key import CreateApiKeyInteractor
from brain.application.interactors.auth.delete_api_key import DeleteApiKeyInteractor
from brain.application.interactors.auth.exceptions import ApiKeyInvalidException, ApiKeyNotFoundException
from brain.application.interactors.auth.get_api_keys import GetApiKeysInteractor
from brain.domain.entities.api_key import ApiKey
from brain.domain.entities.user import User
from brain.presentation.api.dependencies.auth import get_user_from_request
from brain.presentation.api.routes.api_keys.models import (
    ApiKeyValidationSchema,
    ApiKeySchema,
    CreateApiKeySchema,
    ReadApiKeySchema,
)


def _map_api_key_to_schema(api_key: ApiKey) -> ReadApiKeySchema:
    return ReadApiKeySchema(
        id=api_key.id,
        name=api_key.name,
        created_at=api_key.created_at,
    )


@inject
async def create_api_key(
    interactor: FromDishka[CreateApiKeyInteractor],
    body: CreateApiKeySchema,
    user: User = Depends(get_user_from_request),
):
    api_key = await interactor.create_api_key(
        user_id=user.id,
        name=body.name,
    )
    return ApiKeySchema.model_validate(asdict(api_key))


@inject
async def get_api_keys(
    interactor: FromDishka[GetApiKeysInteractor],
    user: User = Depends(get_user_from_request),
):
    api_keys = await interactor.get_api_keys(user_id=user.id)
    return [_map_api_key_to_schema(api_key) for api_key in api_keys]


@inject
async def delete_api_key(
    interactor: FromDishka[DeleteApiKeyInteractor],
    api_key_id: UUID,
    user: User = Depends(get_user_from_request),
):
    try:
        await interactor.delete_api_key(api_key_id=api_key_id, user_id=user.id)
    except ApiKeyNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Api key not found",
        )


@inject
async def validate_api_key(
    interactor: FromDishka[AuthorizeApiKeyInteractor],
    api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required",
        )

    try:
        await interactor.authorize(api_key=api_key)
    except ApiKeyInvalidException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid api key",
        )

    return ApiKeyValidationSchema(is_valid=True)


def get_router() -> APIRouter:
    router = APIRouter(prefix="/api-keys", tags=["Api Keys"])
    router.add_api_route(
        path="/",
        endpoint=create_api_key,
        methods=["POST"],
        response_model=ApiKeySchema,
        status_code=status.HTTP_201_CREATED,
    )
    router.add_api_route(
        path="/",
        endpoint=get_api_keys,
        methods=["GET"],
        response_model=list[ReadApiKeySchema],
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/validate",
        endpoint=validate_api_key,
        methods=["GET"],
        response_model=ApiKeyValidationSchema,
        status_code=status.HTTP_200_OK,
    )
    router.add_api_route(
        path="/{api_key_id}",
        endpoint=delete_api_key,
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
    )
    return router
