from __future__ import annotations


class GSMArenaError(Exception):
    """Base error for GSMArena module."""


class GSMArenaRequestError(GSMArenaError):
    __slots__ = ("status_code", "target_url")

    def __init__(
        self, message: str = "GSMArena request failed", *, status_code: int | None = None, target_url: str | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.target_url = target_url
