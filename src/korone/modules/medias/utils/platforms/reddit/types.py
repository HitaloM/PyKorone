from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from korone.modules.medias.utils.types import MediaSource


@dataclass(frozen=True, slots=True)
class _PostRef:
    kind: str
    name: str | None
    post_id: str


@dataclass(frozen=True, slots=True)
class _ResolvedVideo:
    url: str
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True, slots=True)
class _ScrapedPost:
    author: str
    subreddit: str
    title: str
    post_url: str
    media_sources: list[MediaSource]


@dataclass(frozen=True, slots=True)
class _AnubisChallengeInfo:
    algorithm: str
    difficulty: int
    challenge_id: str
    random_data: str
    pass_url: str
    redir: str
