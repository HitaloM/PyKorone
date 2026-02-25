from __future__ import annotations


class LastFMError(Exception):
    """Base error for Last.fm module."""


class LastFMConfigurationError(LastFMError):
    """Raised when Last.fm client configuration is invalid."""


class LastFMRequestError(LastFMError):
    __slots__ = ("status_code",)

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LastFMPayloadError(LastFMError):
    """Raised when Last.fm payload format is unexpected."""


class LastFMAPIError(LastFMError):
    __slots__ = ("error_code",)

    def __init__(self, message: str, error_code: int | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
