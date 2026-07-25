from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from korone.modules.medias.utils.types import MediaKind


@dataclass(frozen=True, slots=True)
class InstaMedia:
    url: str
    kind: MediaKind
    thumbnail_url: str | None = None


@dataclass(frozen=True, slots=True)
class InstaData:
    media: tuple[InstaMedia, ...]
    username: str
    description: str
