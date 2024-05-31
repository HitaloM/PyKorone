# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

GRAPH_IMAGE = "GraphImage"
GRAPH_VIDEO = "GraphVideo"
STORY_IMAGE = "StoryImage"
STORY_VIDEO = "StoryVideo"

URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/")
REEL_PATTERN = re.compile(r"(?:reel(?:s?)|p)/(?P<post_id>[A-Za-z0-9_-]+)")
STORIES_PATTERN = re.compile(r"(?:stories)/(?:[^/?#&]+/)?(?P<media_id>[0-9]+)")
POST_URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/.*?(?=\s|$)")

TIMEOUT: int = 20
HEADERS: dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
    "Sec-Fetch-Mode": "navigate",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
}
