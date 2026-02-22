from brain.application.services.api_key_authorization import ApiKeyAuthorizationService
from brain.domain.entities.user import User


class AuthorizeApiKeyInteractor:
    def __init__(self, api_key_authorization_service: ApiKeyAuthorizationService):
        self._api_key_authorization_service = api_key_authorization_service

    async def authorize(self, api_key: str) -> User:
        return await self._api_key_authorization_service.authorize(api_key)
