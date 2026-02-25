from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urlparse

from lxml import html as lxml_html

from korone.modules.medias.utils.types import MediaKind

from .constants import INSTAFIX_HOST, INSTAGRAM_HOST


def ensure_url_scheme(url: str) -> str:
    if url.startswith(("http://", "https://")):
        return url
    return f"https://{url.lstrip('/')}"


def build_instafix_url(url: str) -> str:
    if INSTAFIX_HOST in url:
        return url
    return url.replace(INSTAGRAM_HOST, INSTAFIX_HOST)


def build_post_url(url: str) -> str:
    if INSTAFIX_HOST in url:
        return url.replace(INSTAFIX_HOST, INSTAGRAM_HOST)
    return url


def scrape_instafix_data(html_content: str) -> dict[str, str]:
    tree = lxml_html.fromstring(html_content)
    meta_nodes = tree.xpath("//head/meta[@property or @name]")
    scraped: dict[str, str] = {"media_url": "", "username": "", "description": "", "type": ""}

    for node in meta_nodes:
        prop = node.get("property") or node.get("name")
        content = node.get("content")
        if not prop or not content:
            continue

        if prop == "og:video":
            scraped["type"] = "video"
            scraped["media_url"] = build_instafix_media_url(content)
        elif prop == "twitter:title":
            scraped["username"] = content.lstrip("@").strip()
        elif prop == "og:description":
            scraped["description"] = html.unescape(content).strip()
        elif prop == "og:image" and not scraped["media_url"]:
            scraped["type"] = "photo"
            image_url = content.replace("/images/", "/grid/")
            image_url = re.sub(r"/\d+$", "/", image_url)
            scraped["media_url"] = build_instafix_media_url(image_url)

    return scraped


def build_instafix_media_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    return f"https://{INSTAFIX_HOST}{path_or_url}"


def make_filename(url: str, kind: MediaKind) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix
    if not suffix:
        suffix = ".mp4" if kind == MediaKind.VIDEO else ".jpg"
    return f"instagram_media{suffix}"
