# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, HttpUrl


class TikTokSlideshow(BaseModel):
    author: str
    desc: str
    images: list[HttpUrl]
    music_url: HttpUrl | str


class TikTokVideo(BaseModel):
    author: str
    desc: str
    width: int
    height: int
    duration: int
    video_url: HttpUrl
    thumbnail_url: HttpUrl
