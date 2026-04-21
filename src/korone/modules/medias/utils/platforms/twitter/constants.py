from __future__ import annotations

import re

FXTWITTER_STATUS_API = "https://api.fxtwitter.com/2/status/{status_id}"

PATTERN = re.compile(
    r"https?://(?:www\.)?(?:x\.com|(?:www\.|mobile\.)?twitter\.com)/"
    r"(?:i/(?:web/)?|[A-Za-z0-9_]{1,15}/)?status/\d+"
    r"(?:/[^\s?#]+)?(?:\?[^\s#]*)?(?:#[^\s]*)?",
    re.IGNORECASE,
)
