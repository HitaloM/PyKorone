import re
from typing import Final

import aiohttp

PATTERN: Final[re.Pattern[str]] = re.compile(
    r"https?://(?:www\.)?example\.com/posts/(?P<id>[A-Za-z0-9_-]+)", re.IGNORECASE
)
API_URL: Final[str] = "https://api.example.com/posts/{post_id}"
REQUEST_TIMEOUT: Final[aiohttp.ClientTimeout] = aiohttp.ClientTimeout(total=60, connect=15)
RETRYABLE_STATUSES: Final[frozenset[int]] = frozenset({408, 425, 429, 500, 502, 503, 504})
