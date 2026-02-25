from __future__ import annotations

import re

BSKY_PUBLIC_API = "https://public.api.bsky.app/xrpc"
BSKY_RESOLVE_HANDLE = f"{BSKY_PUBLIC_API}/com.atproto.identity.resolveHandle"
BSKY_POST_THREAD = f"{BSKY_PUBLIC_API}/app.bsky.feed.getPostThread"
BSKY_PLC_DIRECTORY = "https://plc.directory"
HTTP_TIMEOUT = 25

PATTERN = re.compile(
    r"https?://(?:www\.)?bsky\.app/profile/(?P<handle>[^/]+)/post/(?P<rkey>[A-Za-z0-9]+)(?:\?[^\s]+)?", re.IGNORECASE
)
