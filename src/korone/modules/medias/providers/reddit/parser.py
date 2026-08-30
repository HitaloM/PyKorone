import html
import re
from typing import TYPE_CHECKING
from urllib.parse import urldefrag, urljoin, urlparse

from korone.modules.medias.parsing import coerce_int, coerce_str, ensure_url_scheme

from .constants import POST_TYPE_REGEX

if TYPE_CHECKING:
    from lxml import html as lxml_html


def normalize_post_id(post_id: str) -> str | None:
    candidate = post_id.strip()
    if not candidate:
        return None
    if re.fullmatch(r"[A-Za-z0-9]+", candidate):
        return candidate
    return None


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


def extract_post_type(html_content: str) -> str:
    match = POST_TYPE_REGEX.search(html_content)
    return match.group(1).strip().lower() if match else ""


def extract_node_text(tree: lxml_html.HtmlElement, xpath: str) -> str:
    nodes = tree.xpath(xpath)
    if not nodes:
        return ""
    first = nodes[0]
    text = first.text_content() if hasattr(first, "text_content") else str(first)
    return " ".join(text.split()).strip()


def extract_title(tree: lxml_html.HtmlElement) -> str:
    title_parts = tree.xpath("//h1[contains(@class, 'post_title')]/text()")
    return " ".join(part.strip() for part in title_parts if isinstance(part, str) and part.strip())


def extract_gallery_urls(tree: lxml_html.HtmlElement) -> list[str]:
    urls: list[str] = []
    for figure in tree.xpath("//div[contains(@class, 'gallery')]//figure"):
        href = first_non_empty(figure.xpath(".//a/@href"))
        src = first_non_empty(figure.xpath(".//img[@alt='Gallery image']/@src"))
        if selected := href or src:
            urls.append(selected)
    return urls


def extract_image_url(tree: lxml_html.HtmlElement) -> str | None:
    return (
        first_non_empty(
            tree.xpath("//div[contains(@class, 'post_media_content')]//a[contains(@class, 'post_media_image')]/@href")
        )
        or first_non_empty(tree.xpath("//div[contains(@class, 'post_media_content')]//img/@src"))
        or first_non_empty(tree.xpath("//meta[@property='og:image']/@content"))
    )


def extract_video_duration_seconds(video_node: lxml_html.HtmlElement) -> int | None:
    for raw_duration in (
        video_node.get("duration"),
        video_node.get("data-duration"),
        video_node.get("data-video-duration"),
        video_node.get("data-length"),
        video_node.get("data-video-length"),
    ):
        duration = coerce_int(raw_duration)
        if duration and duration > 0:
            return duration
        if isinstance(raw_duration, str) and (clock_duration := parse_clock_duration_seconds(raw_duration)) is not None:
            return clock_duration
    return None


def parse_clock_duration_seconds(raw_duration: str) -> int | None:
    normalized = raw_duration.strip()
    if ":" not in normalized:
        return None

    parts = normalized.split(":")
    if len(parts) not in {2, 3} or any(not part.isdigit() for part in parts):
        return None

    total = 0
    for part in parts:
        total = (total * 60) + int(part)
    return total if total > 0 else None
