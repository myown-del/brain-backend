from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import HTTPException, Header
from starlette import status

from brain.application.interactors.auth.exceptions import (
    ApiKeyInvalidException,
    AuthorizationHeaderRequiredException,
    JwtTokenExpiredException,
    JwtTokenInvalidException,
)
from brain.application.interactors.auth.interactor import AuthInteractor
from brain.application.interactors.auth.request_authorization import RequestAuthorizationInteractor


def _extract_bearer_token(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("Bearer "):
        return value.replace("Bearer ", "", 1)
    return value


@inject
async def get_user_from_request(
    auth_interactor: FromDishka[AuthInteractor],
    token: str | None = Header(default=None, alias="Authorization"),
):
    token = _extract_bearer_token(token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )

    try:
        return await auth_interactor.authorize_by_token(token)
    except JwtTokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JwtTokenInvalidException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


@inject
async def get_notes_user_from_request(
    request_authorization_interactor: FromDishka[RequestAuthorizationInteractor],
    token: str | None = Header(default=None, alias="Authorization"),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    try:
        return await request_authorization_interactor.authorize(
            authorization_header=token,
            api_key_header=api_key,
        )
    except AuthorizationHeaderRequiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
        )
    except ApiKeyInvalidException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid api key",
        )
    except JwtTokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JwtTokenInvalidException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
