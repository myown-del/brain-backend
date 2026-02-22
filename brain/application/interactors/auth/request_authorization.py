from brain.application.interactors.auth.exceptions import ApiKeyInvalidException, AuthorizationHeaderRequiredException
from brain.application.services.api_key_authorization import ApiKeyAuthorizationService
from brain.application.services.auth_tokens import AuthTokensService
from brain.domain.entities.user import User


class RequestAuthorizationInteractor:
    def __init__(
        self,
        auth_tokens_service: AuthTokensService,
        api_key_authorization_service: ApiKeyAuthorizationService,
    ):
        self._auth_tokens_service = auth_tokens_service
        self._api_key_authorization_service = api_key_authorization_service

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
                return await self._api_key_authorization_service.authorize(api_key_header)
            except ApiKeyInvalidException:
                if not authorization_header:
                    raise

        token = self._extract_bearer_token(authorization_header)
        if not token:
            raise AuthorizationHeaderRequiredException()

        return await self._auth_tokens_service.authorize_by_token(token)
