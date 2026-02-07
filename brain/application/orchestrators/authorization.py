from brain.application.interactors.auth.authorize_api_key import (
    AuthorizeApiKeyInteractor,
)
from brain.application.interactors.auth.exceptions import (
    ApiKeyInvalidException,
    AuthorizationHeaderRequiredException,
)
from brain.application.interactors.auth.interactor import AuthInteractor
from brain.domain.entities.user import User


class AuthorizationOrchestrator:
    def __init__(
        self,
        auth_interactor: AuthInteractor,
        api_key_interactor: AuthorizeApiKeyInteractor,
    ):
        self._auth_interactor = auth_interactor
        self._api_key_interactor = api_key_interactor

    @staticmethod
    def _extract_bearer_token(value: str | None) -> str | None:
        if not value:
            return None
        if value.startswith("Bearer "):
            return value.replace("Bearer ", "", 1)
        return value

    async def authorize(
        self,
        authorization_header: str | None,
        api_key_header: str | None,
    ) -> User:
        if api_key_header:
            try:
                return await self._api_key_interactor.authorize(api_key_header)
            except ApiKeyInvalidException:
                if not authorization_header:
                    raise

        token = self._extract_bearer_token(authorization_header)
        if not token:
            raise AuthorizationHeaderRequiredException()

        return await self._auth_interactor.authorize_by_token(token)
