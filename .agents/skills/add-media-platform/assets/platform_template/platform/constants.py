import re

import aiohttp

PATTERN = re.compile(r"https?://(?:www\.)?example\.com/posts/(?P<id>[A-Za-z0-9_-]+)", re.IGNORECASE)
API_URL = "https://api.example.com/posts/{post_id}"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=60, connect=15)
