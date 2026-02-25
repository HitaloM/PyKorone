from __future__ import annotations

import re
from urllib.parse import urlparse

REDLIB_INSTANCES = ("https://redlib.catsarch.com", "https://redlib.4o1x5.dev", "https://l.opnxng.com")
REDDIT_PATTERN_HOSTS = tuple(urlparse(instance).netloc for instance in REDLIB_INSTANCES)
REDDIT_PATTERN_HOSTS_REGEX = "|".join(re.escape(host) for host in REDDIT_PATTERN_HOSTS)
ANUBIS_PASS_CHALLENGE_PATH = "/.within.website/x/cmd/anubis/api/pass-challenge"
REDLIB_REQUEST_COOKIES = {"use_hls": "on", "hide_hls_notification": "on"}

PATTERN = re.compile(
    rf"https?://(?:"
    rf"(?:www\.|old\.|new\.|np\.)?reddit\.com/(?:(?:r|user)/[^/\s]+/comments/[A-Za-z0-9]+(?:/[^\s?#]*)?|comments/[A-Za-z0-9]+(?:/[^\s?#]*)?)"
    rf"|(?:www\.)?redd\.it/[A-Za-z0-9]+(?:/[^\s?#]*)?"
    rf"|(?:{REDDIT_PATTERN_HOSTS_REGEX}|(?:[A-Za-z0-9-]+\.)?redlib\.[A-Za-z0-9.-]+)/(?:(?:r|user)/[^/\s]+/comments/[A-Za-z0-9]+(?:/[^\s?#]*)?|comments/[A-Za-z0-9]+(?:/[^\s?#]*)?)"
    rf")(?:\?[^\s#]*)?(?:#[^\s]*)?",
    re.IGNORECASE,
)

POST_TYPE_REGEX = re.compile(r"post_type:\s*(\w+)", re.IGNORECASE)
VIDEO_REGEX = re.compile(r'(?s)<source\s+[^>]*src="([^"]+)"[^>]*type="video/mp4"')
PLAYLIST_REGEX = re.compile(r'(?s)<source\s+[^>]*src="([^"]+)"[^>]*type="application/vnd\.apple\.mpegurl"')
JSON_SCRIPT_REGEX_TEMPLATE = r'(?is)<script[^>]*\bid=["\']{script_id}["\'][^>]*>(.*?)</script>'
META_REFRESH_REGEX = re.compile(r'(?is)<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\']([^"\']+)["\']')
BLOCK_MARKERS = ("anubis_challenge", "making sure you're not a bot", "<title>403")
