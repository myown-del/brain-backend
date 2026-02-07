class JwtTokenExpiredException(Exception):
    pass


class JwtTokenInvalidException(Exception):
    pass


class TelegramBotAuthSessionNotFoundException(Exception):
    pass


class ApiKeyInvalidException(Exception):
    pass


class ApiKeyNotFoundException(Exception):
    pass


class AuthorizationHeaderRequiredException(Exception):
    pass
