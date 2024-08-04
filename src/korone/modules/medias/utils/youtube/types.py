# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, Field, FilePath, HttpUrl, field_validator


class VideoInfo(BaseModel):
    title: str
    video_id: str = Field(alias="id")
    thumbnail: FilePath | None = None
    url: HttpUrl | None = None
    duration: int = 0
    view_count: int = 0
    like_count: int = 0
    uploader: str
    height: int
    width: int

    @field_validator("height", "width", mode="before")
    @classmethod
    def validate_dimensions(cls, v):
        if not isinstance(v, int):
            return 0
        return v
