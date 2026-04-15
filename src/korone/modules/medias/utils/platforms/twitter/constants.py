from __future__ import annotations

import re

FXTWITTER_STATUS_API = "https://api.fxtwitter.com/status/{status_id}"
FXTWITTER_STATUS_API_WITH_HANDLE = "https://api.fxtwitter.com/{handle}/status/{status_id}"

PATTERN = re.compile(
    r"https?://(?:www\.)?(?:x\.com|(?:www\.|mobile\.)?twitter\.com)/"
    r"(?:i/(?:web/)?|[A-Za-z0-9_]{1,15}/)?status/\d+"
    r"(?:/[^\s?#]+)?(?:\?[^\s#]*)?(?:#[^\s]*)?",
    re.IGNORECASE,
)
