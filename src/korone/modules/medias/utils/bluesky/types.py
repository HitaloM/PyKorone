# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, Field, HttpUrl


class AspectRatio(BaseModel):
    height: int | None = None
    width: int | None = None


class Image(BaseModel):
    thumb: str
    fullsize: HttpUrl
    alt: str | None = None
    aspect_ratio: AspectRatio | None = Field(None, alias="aspectRatio")


class Embed(BaseModel):
    embed_type: str | None = Field(None, alias="$type")
    images: list[Image] | None = None
    playlist: str | None = None
    thumbnail: HttpUrl | None = None
    aspect_ratio: AspectRatio | None = Field(None, alias="aspectRatio")


class Record(BaseModel):
    text: str | None = Field(None, alias="text")


class Author(BaseModel):
    handle: str
    display_name: str | None = Field(None, alias="displayName")


class Post(BaseModel):
    uri: str
    cid: str
    author: Author
    record: Record
    embed: Embed | None = None


class Thread(BaseModel):
    post: Post


class BlueskyData(BaseModel):
    thread: Thread
