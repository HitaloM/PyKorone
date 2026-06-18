import html
import re
from urllib.parse import urldefrag, urljoin, urlparse

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


def is_share_url(url: str) -> bool:
    parsed = urlparse(ensure_url_scheme(url))
    host = (parsed.hostname or "").casefold()
    if host != "reddit.com" and not host.endswith(".reddit.com"):
        return False

    segments = [segment for segment in parsed.path.split("/") if segment]
    return (
        len(segments) == 4
        and segments[0].casefold() in {"r", "user"}
        and bool(segments[1])
        and segments[2].casefold() == "s"
        and re.fullmatch(r"[A-Za-z0-9_-]+", segments[3]) is not None
    )


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
