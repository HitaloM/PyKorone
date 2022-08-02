# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import re

from yt_dlp import YoutubeDL

YOUTUBE_REGEX = re.compile(
    r"(?m)http(?:s?):\/\/(?:www\.)?(?:music\.)?youtu(?:be\.com\/(watch\?v=|shorts/)|\.be\/|)([\w\-\_]*)(&(amp;)?[\w\?=]*)?"
)
PLAYLIST_REGEX = re.compile(rf".*({YOUTUBE_REGEX}\/|list=)([^#\&\?]*).*")
TIME_REGEX = re.compile(r"[?&]t=([0-9]+)")

TWITTER_REGEX = re.compile(
    r"https?://(?:(?:www|m(?:obile)?)\.)?twitter\.com/(?:(?:i/web|[^/]+)/status|statuses)/(?P<id>\d+)"
)


def extract_info(instance: YoutubeDL, url: str, download=True):
    return instance.extract_info(url, download)
