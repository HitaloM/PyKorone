# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from enum import StrEnum

from hairydogm.filters.callback_data import CallbackData


class YtMediaType(StrEnum):
    Video = "video"
    Audio = "audio"


class YtGetCallback(CallbackData, prefix="ytdl"):
    media_id: str
    media_type: YtMediaType
