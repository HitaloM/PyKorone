from __future__ import annotations

import re

WEB_VIDEO_DETAIL_URL = "https://www.tiktok.com/@i/video/{post_id}"
UNIVERSAL_DATA_SCRIPT_ID = "__UNIVERSAL_DATA_FOR_REHYDRATION__"
WEBAPP_DEFAULT_SCOPE_KEY = "__DEFAULT_SCOPE__"
WEBAPP_VIDEO_SCOPE_KEY = "webapp.video-detail"
PLAY_URL_MARKER = "/aweme/v1/play/"
MAX_REDIRECTS = 5

TIKTOK_WEB_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/132.0.0.0 Safari/537.36"
    ),
}

TIKTOK_MEDIA_HEADERS = {
    "Accept": "*/*",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.3"
    ),
}

PATTERN = re.compile(
    r"https?://(?:"
    r"(?:www\.|m\.)?tiktok\.com/(?:@[^/\s]+/(?:video|photo|live)/[A-Za-z0-9._-]+|v/[A-Za-z0-9._-]+|t/[A-Za-z0-9._-]+)"
    r"|(?:vm|vt)\.tiktok\.com/[A-Za-z0-9._-]+/?"
    r")(?:\?[^\s#]*)?(?:#[^\s]*)?",
    re.IGNORECASE,
)

POST_ID_PATTERN = re.compile(r"/(?:video|photo|v)/(?P<id>\d{1,19})", re.IGNORECASE)

UNIVERSAL_DATA_SCRIPT_PATTERN = re.compile(
    rf"<script[^>]*id=[\"']{re.escape(UNIVERSAL_DATA_SCRIPT_ID)}[\"'][^>]*>(?P<payload>.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
