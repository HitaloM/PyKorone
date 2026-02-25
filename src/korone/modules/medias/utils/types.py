from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import InputFile


class MediaKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"


@dataclass(frozen=True, slots=True)
class MediaItem:
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
    media: list[MediaItem]


@dataclass(frozen=True, slots=True)
class MediaSource:
    kind: MediaKind
    url: str
    thumbnail_url: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
