from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import re

    from aiogram.types import InputFile


class MediaKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"


class MediaStage(StrEnum):
    RESOLVE = "resolve"
    CACHE_SEND = "cache_send"
    FETCH = "fetch"
    SEND = "send"
    CACHE_STORE = "cache_store"


class MediaOutcome(StrEnum):
    IGNORED = "ignored"
    CACHED = "cached"
    NOT_FOUND = "not_found"
    SEND_FAILED = "send_failed"
    SENT = "sent"
    CANCELLED = "cancelled"
    SEND_TIMEOUT = "send_timeout"
    RATE_LIMITED = "rate_limited"
    PERMISSION_DENIED = "permission_denied"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    key: str
    name: str
    website: str
    pattern: re.Pattern[str]
    author_handle_prefix: str = "@"
    show_author_name: bool = True


@dataclass(frozen=True, slots=True)
class MediaSource:
    kind: MediaKind
    url: str
    thumbnail_url: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    audio_url: str | None = None
    fallback_url: str | None = None


@dataclass(frozen=True, slots=True)
class PreparedMedia:
    kind: MediaKind
    file: InputFile | str
    filename: str
    source_url: str
    thumbnail: InputFile | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True, slots=True)
class MediaPost:
    author_name: str
    author_handle: str
    text: str
    url: str
    website: str
    media: tuple[PreparedMedia, ...]
    quote_text: str | None = None
    quote_author_name: str | None = None
    quote_author_handle: str | None = None


class MediaProvider(Protocol):
    info: ProviderInfo

    async def fetch(self, url: str) -> MediaPost | None: ...


@dataclass(frozen=True, slots=True)
class MediaRequest:
    provider: MediaProvider
    url: str


@dataclass(frozen=True, slots=True)
class DeliveredMedia:
    media: PreparedMedia
    file_id: str


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    media: tuple[DeliveredMedia, ...]
