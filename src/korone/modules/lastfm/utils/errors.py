from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiohttp import ClientResponse


class LastFMError(Exception):
    def __init__(self, message: str, error_code: int | None = None, response: ClientResponse | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.response = response


class ServiceUnavailableError(LastFMError):
    pass


class AuthenticationFailedError(LastFMError):
    pass


class InvalidResponseFormatError(LastFMError):
    pass


class ParameterError(LastFMError):
    pass


class RateLimitExceededError(LastFMError):
    pass


class InvalidResourceError(LastFMError):
    pass


class GenericError(LastFMError):
    pass


class ServiceOfflineError(LastFMError):
    pass


class TemporaryError(LastFMError):
    pass


class APIKeyBannedError(LastFMError):
    pass


ERROR_CODE_MAP: dict[int | None, type[LastFMError]] = {
    2: ServiceUnavailableError,
    4: AuthenticationFailedError,
    5: InvalidResponseFormatError,
    6: ParameterError,
    7: InvalidResourceError,
    8: GenericError,
    11: ServiceOfflineError,
    16: TemporaryError,
    26: APIKeyBannedError,
    29: RateLimitExceededError,
    None: LastFMError,
}
