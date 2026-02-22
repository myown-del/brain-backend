import hashlib
import hmac
import os
import re
from base64 import b64decode, b64encode


_PIN_PATTERN = re.compile(r"^\d{4,6}$")
_SALT_SIZE = 16
_HASH_LENGTH = 32
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


class InvalidPinFormatException(Exception):
    pass


class PinVerificationService:
    def _validate_pin(self, pin: str) -> None:
        if not _PIN_PATTERN.fullmatch(pin):
            raise InvalidPinFormatException()

    def hash_pin(self, pin: str) -> str:
        self._validate_pin(pin)

        salt = os.urandom(_SALT_SIZE)
        key = hashlib.scrypt(
            pin.encode("utf-8"),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=_HASH_LENGTH,
        )
        encoded_salt = b64encode(salt).decode("ascii")
        encoded_key = b64encode(key).decode("ascii")
        return f"scrypt:{_SCRYPT_N}:{_SCRYPT_R}:{_SCRYPT_P}:{encoded_salt}:{encoded_key}"

    def verify_pin(self, pin: str, stored_hash: str | None) -> bool:
        self._validate_pin(pin)
        if not stored_hash:
            return False

        try:
            method, n, r, p, encoded_salt, encoded_key = stored_hash.split(":")
            if method != "scrypt":
                return False

            key = hashlib.scrypt(
                pin.encode("utf-8"),
                salt=b64decode(encoded_salt.encode("ascii")),
                n=int(n),
                r=int(r),
                p=int(p),
                dklen=len(b64decode(encoded_key.encode("ascii"))),
            )
            return hmac.compare_digest(
                key,
                b64decode(encoded_key.encode("ascii")),
            )
        except (ValueError, TypeError):
            return False
