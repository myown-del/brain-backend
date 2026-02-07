import hashlib
import secrets
import string

from brain.domain.services.api_keys import IApiKeyService


class ApiKeyService(IApiKeyService):
    _KEY_LENGTH = 32
    _ALPHABET = string.ascii_letters + string.digits

    def generate_key(self) -> str:
        return "".join(secrets.choice(self._ALPHABET) for _ in range(self._KEY_LENGTH))

    def hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()
