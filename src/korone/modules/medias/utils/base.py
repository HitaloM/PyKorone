from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    import re

    from aiogram.types import InputFile


class MediaKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"


@dataclass(frozen=True, slots=True)
class MediaItem:
    kind: MediaKind
    file: InputFile
    filename: str


@dataclass(frozen=True, slots=True)
class MediaPost:
    author_name: str
    author_handle: str
    text: str
    url: str
    website: str
    media: list[MediaItem]


class MediaProvider(ABC):
    name: ClassVar[str]
    website: ClassVar[str]
    pattern: ClassVar[re.Pattern[str]]

    @classmethod
    def extract_urls(cls, text: str) -> list[str]:
        return [match.group(0) for match in cls.pattern.finditer(text)]

    @classmethod
    @abstractmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        raise NotImplementedError
