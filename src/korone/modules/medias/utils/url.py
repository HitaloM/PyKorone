from __future__ import annotations

from functools import lru_cache
from urllib.parse import urldefrag, urlsplit, urlunsplit

from url_normalize import url_normalize


def normalize_media_url(url: str) -> str | None:
    candidate = url.strip()
    if not candidate:
        return None

    return _normalize_media_url_cached(candidate)


@lru_cache(maxsize=4096)
def _normalize_media_url_cached(candidate: str) -> str | None:
    if not candidate:
        return None

    try:
        normalized = url_normalize(candidate, default_scheme="https", filter_params=True)
    except ValueError:
        return None

    if not normalized:
        return None

    without_fragment, _ = urldefrag(normalized)
    parsed = urlsplit(without_fragment)
    if not parsed.netloc:
        return None

    path = parsed.path
    if path and path != "/":
        path = path.rstrip("/")
    if not path:
        path = "/"

    return urlunsplit(parsed._replace(path=path))
