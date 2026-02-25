from __future__ import annotations

import re

TIKTOK_FEED_API = "https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/"
TIKTOK_IMAGE_AWEME_TYPES = {2, 68, 150}

TIKTOK_QUERY_PARAMS = {
    "iid": "7318518857994389254",
    "device_id": "7318517321748022790",
    "channel": "googleplay",
    "version_code": "300904",
    "device_platform": "android",
    "device_type": "ASUS_Z01QD",
    "os_version": "9",
    "aid": "1128",
}

TIKTOK_API_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "identity",
    "Accept-Language": "en",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Sec-Ch-UA": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-UA-Mobile": "?0",
    "Sec-Ch-UA-Platform": '"Windows"',
}

PATTERN = re.compile(
    r"https?://(?:"
    r"(?:www\.|m\.)?tiktok\.com/(?:@[^/\s]+/(?:video|photo)/\d+|v/\d+|t/[A-Za-z0-9._-]+)"
    r"|(?:vm|vt)\.tiktok\.com/[A-Za-z0-9._-]+/?"
    r")(?:\?[^\s#]*)?(?:#[^\s]*)?",
    re.IGNORECASE,
)

POST_ID_PATTERN = re.compile(r"/(?:video|photo|v)/(?P<id>\d+)", re.IGNORECASE)
