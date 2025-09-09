# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class VideoInfo(BaseModel):
    title: str
    video_id: str = Field(alias="id")
    thumbnail: str | HttpUrl | None = None
    url: HttpUrl | None = None
    duration: int = 0
    view_count: int = 0
    like_count: int | None = None
    uploader: str
    height: int = 0
    width: int = 0

    @field_validator("height", "width", mode="before")
    @classmethod
    def validate_dimensions(cls, v: Any) -> int:
        if v is None:
            return 0
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0
