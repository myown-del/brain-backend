from dishka import Provider, Scope, provide

from brain.domain.services.api_keys import IApiKeyService
from brain.infrastructure.api_keys.service import ApiKeyService


class ApiKeyServiceProvider(Provider):
    api_key_service = provide(ApiKeyService, scope=Scope.APP, provides=IApiKeyService)
