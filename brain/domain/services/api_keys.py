from typing import Protocol


class IApiKeyService(Protocol):
    def generate_key(self) -> str:
        raise NotImplementedError

    def hash_key(self, key: str) -> str:
        raise NotImplementedError
