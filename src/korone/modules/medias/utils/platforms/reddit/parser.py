from __future__ import annotations

import html
import re
from urllib.parse import urldefrag, urljoin


def normalize_post_id(post_id: str) -> str | None:
    candidate = post_id.strip()
    if not candidate:
        return None
    if re.fullmatch(r"[A-Za-z0-9]+", candidate):
        return candidate
    return None


def ensure_url_scheme(url: str) -> str:
    if url.startswith(("http://", "https://")):
        return url
    return f"https://{url.lstrip('/')}"


def looks_like_block_page(html_content: str, markers: tuple[str, ...]) -> bool:
    lowered = html_content.lower()
    return any(marker in lowered for marker in markers)


def normalize_media_url(base_url: str, candidate: str | None) -> str:
    if not candidate:
        return ""

    decoded = html.unescape(candidate.strip())
    if not decoded:
        return ""

    absolute = urljoin(base_url, decoded)
    absolute, _ = urldefrag(absolute)
    return absolute.strip()


def first_non_empty(values: list[str]) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def coerce_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None
