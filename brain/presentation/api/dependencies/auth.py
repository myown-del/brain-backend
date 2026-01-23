from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import HTTPException, Header, Depends
from starlette import status

from brain.application.interactors.auth.exceptions import JwtTokenExpiredException, JwtTokenInvalidException
from brain.application.interactors.auth.interactor import AuthInteractor


@inject
async def get_user_from_request(
    auth_interactor: FromDishka[AuthInteractor],
    token: str = Header(alias="Authorization"),
):
    if "Bearer " in token:
        token = token.replace("Bearer ", "")

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
