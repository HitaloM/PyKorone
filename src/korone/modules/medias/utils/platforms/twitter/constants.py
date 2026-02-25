from __future__ import annotations

import re

FXTWITTER_API = "https://api.fxtwitter.com/status/{status_id}"

PATTERN = re.compile(
    r"https?://(?:www\.)?(?:x\.com|twitter\.com)/(?:i/web/)?(?:[A-Za-z0-9_]{1,15}/)?status/\d+(?:/[^\s?]+)?(?:\?[^\s]+)?",
    re.IGNORECASE,
)
