# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True, slots=True)
class TikTokSlideshow:
    author: str
    desc: str
    images: list[BinaryIO]
    music_url: str


@dataclass(frozen=True, slots=True)
class TikTokVideo:
    author: str
    desc: str
    width: int
    height: int
    duration: int
    video_file: BinaryIO
    thumbnail_file: BinaryIO
