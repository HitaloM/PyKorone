# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Website(BaseModel):
    url: HttpUrl | str
    display_url: str


class Author(BaseModel):
    author_id: str = Field(alias="id")
    name: str
    screen_name: str
    avatar_url: HttpUrl | str
    banner_url: HttpUrl | str
    description: str
    location: str
    url: HttpUrl | None = None
    followers: int
    following: int
    joined: str
    likes: int
    website: Website | None = None
    tweets: int
    avatar_color: str | None = None


class MediaVariants(BaseModel):
    content_type: str
    bitrate: int | None = None
    url: HttpUrl


class Media(BaseModel):
    url: HttpUrl
    thumbnail_url: HttpUrl | None = None
    duration: int = 0
    width: int
    height: int
    media_format: str | None = Field(default=None, alias="format")
    media_type: str = Field(alias="type")
    variants: list[MediaVariants] | None = None

    @field_validator("duration", mode="before")
    @classmethod
    def validate_duration(cls, v: Any) -> int:
        if isinstance(v, float):
            v = int(v)
        return v


class MediaContainer(BaseModel):
    all_medias: list[Media] | None = Field(default=None, alias="all")
    videos: list[Media] | None = None
    photos: list[Media] | None = None


class Reference(BaseModel):
    ref_type: str = Field(alias="type")
    url: HttpUrl
    url_type: str = Field(alias="urlType")


class Entities(BaseModel):
    from_index: int = Field(alias="fromIndex")
    to_index: int = Field(alias="toIndex")
    ref: Reference | None = None


class CommunityNote(BaseModel):
    text: str
    entities: list[Entities] | None = None


class Tweet(BaseModel):
    url: HttpUrl
    tweet_id: str = Field(alias="id")
    text: str
    author: Author
    replies: int
    retweets: int
    likes: int
    created_at: str
    created_timestamp: int
    possibly_sensitive: bool = False
    views: int | None = None
    is_note_tweet: bool
    community_note: CommunityNote | None = None
    lang: str | None = None
    replying_to: str | None = None
    replying_to_status: str | None = None
    quote: Tweet | None = None
    media: MediaContainer | None = None
    source: str | None = None
    twitter_card: str | None = None
    color: str | None = None


class Response(BaseModel):
    code: int
    message: str
    tweet: Tweet | None = None
