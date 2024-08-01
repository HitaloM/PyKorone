# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True, slots=True)
class TweetAuthor:
    name: str
    screen_name: str


@dataclass(frozen=True, slots=True)
class TweetMediaVariants:
    content_type: str
    bitrate: int
    url: str
    binary_io: BinaryIO


@dataclass(frozen=True, slots=True)
class TweetMedia:
    type: str
    format: str
    url: str
    binary_io: BinaryIO
    duration: int
    width: int
    height: int
    thumbnail_io: BinaryIO | None
    thumbnail_url: str
    variants: list[TweetMediaVariants]


@dataclass(frozen=True, slots=True)
class TweetData:
    url: str
    text: str
    author: TweetAuthor
    replies: int
    retweets: int
    likes: int
    created_at_timestamp: int
    media: list[TweetMedia]
    source: str
