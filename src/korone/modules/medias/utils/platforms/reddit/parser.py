from __future__ import annotations

import html
import re
from urllib.parse import urldefrag, urljoin

from korone.modules.medias.utils import parsing as shared_parsing
from korone.modules.medias.utils.parsing import coerce_str


def normalize_post_id(post_id: str) -> str | None:
    candidate = post_id.strip()
    if not candidate:
        return None
    if re.fullmatch(r"[A-Za-z0-9]+", candidate):
        return candidate
    return None


def ensure_url_scheme(url: str) -> str:
    return shared_parsing.ensure_url_scheme(url)


def looks_like_block_page(html_content: str, markers: tuple[str, ...]) -> bool:
    lowered = html_content.lower()
    return any(marker in lowered for marker in markers)


def normalize_media_url(base_url: str, candidate: str | None) -> str:
    if not candidate:
        return ""

    decoded = coerce_str(html.unescape(candidate))
    if not decoded:
        return ""

    absolute = urljoin(base_url, decoded)
    absolute, _ = urldefrag(absolute)
    return coerce_str(absolute) or ""


def first_non_empty(values: list[str]) -> str | None:
    for value in values:
        if normalized := coerce_str(value):
            return normalized
    return None
