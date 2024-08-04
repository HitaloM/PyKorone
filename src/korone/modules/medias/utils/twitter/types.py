# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, Field, HttpUrl, PositiveInt, TypeAdapter, field_validator

url_adapter = TypeAdapter(HttpUrl)


class Website(BaseModel):
    url: HttpUrl
    display_url: str


class TweetAuthor(BaseModel):
    author_id: str = Field(alias="id")
    name: str
    screen_name: str
    avatar_url: HttpUrl
    banner_url: HttpUrl
    description: str
    location: str
    url: Website | str | None = None
    followers: PositiveInt
    following: PositiveInt
    joined: str
    likes: PositiveInt
    website: Website | str | None = None
    tweets: PositiveInt
    avatar_color: str | None = None

    @field_validator("url", "website", mode="before")
    @classmethod
    def validate_website(cls, v):
        if isinstance(v, dict):
            return Website(**v)
        if isinstance(v, str):
            return Website(
                url=url_adapter.validate_python(v),
                display_url=str(v),
            )
        return v


class TweetMediaVariants(BaseModel):
    content_type: str
    bitrate: int | None = None
    url: HttpUrl


class TweetMedia(BaseModel):
    url: HttpUrl
    thumbnail_url: HttpUrl | None = None
    duration: float = 0
    width: PositiveInt
    height: PositiveInt
    media_format: str | None = Field(default=None, alias="format")
    media_type: str = Field(alias="type")
    variants: list[TweetMediaVariants] | None = None


class TweetMediaContainer(BaseModel):
    all_medias: list[TweetMedia] = Field(default_factory=list, alias="all")
    videos: list[TweetMedia] | None = None
    photos: list[TweetMedia] | None = None


class Tweet(BaseModel):
    url: HttpUrl
    tweet_id: str = Field(alias="id")
    text: str = ""
    author: TweetAuthor
    replies: PositiveInt
    retweets: PositiveInt
    likes: PositiveInt
    created_at: str
    created_timestamp: PositiveInt
    possibly_sensitive: bool
    views: PositiveInt
    is_note_tweet: bool
    community_note: str | None = None
    lang: str
    replying_to: str | None = None
    replying_to_status: str | None = None
    media: TweetMediaContainer
    source: str
    twitter_card: str
    color: str | None = None


class Response(BaseModel):
    code: PositiveInt
    message: str
    tweet: Tweet | None = None
