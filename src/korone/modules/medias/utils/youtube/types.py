# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VideoInfo:
    title: str
    video_id: str
    thumbnail: str | None
    url: str
    duration: int
    view_count: int
    like_count: int
    uploader: str
    height: int
    width: int
