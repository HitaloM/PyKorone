from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import urlparse

from lxml import html as lxml_html

from korone.modules.medias.utils.parsing import coerce_str, ensure_url_scheme
from korone.modules.medias.utils.types import MediaKind

from .constants import INSTAFIX_HOST, INSTAGRAM_HOST
from .types import InstaData


def build_instafix_url(url: str) -> str:
    if INSTAFIX_HOST in url:
        return url
    return url.replace(INSTAGRAM_HOST, INSTAFIX_HOST)


def build_post_url(url: str) -> str:
    if INSTAFIX_HOST in url:
        return url.replace(INSTAFIX_HOST, INSTAGRAM_HOST)
    return url


def scrape_instafix_data(html_content: str) -> InstaData | None:
    tree = lxml_html.fromstring(html_content)
    meta_nodes = tree.xpath("//head/meta[@property or @name]")

    media_url = ""
    username = ""
    description = ""
    media_type = ""

    for node in meta_nodes:
        prop = coerce_str(node.get("property") or node.get("name"))
        content = coerce_str(node.get("content"))
        if not prop or not content:
            continue

        if prop == "og:video":
            media_type = "video"
            media_url = build_instafix_media_url(content)
        elif prop == "twitter:title":
            username = content.lstrip("@")
        elif prop == "og:description":
            description = coerce_str(html.unescape(content)) or ""
        elif prop == "og:image" and not media_url:
            media_type = "photo"
            image_url = content.replace("/images/", "/grid/")
            image_url = re.sub(r"/\d+$", "/", image_url)
            media_url = build_instafix_media_url(image_url)

    if not media_url:
        return None

    return InstaData(media_url=media_url, username=username, description=description, media_type=media_type)


def build_instafix_media_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        return ensure_url_scheme(path_or_url)
    return ensure_url_scheme(f"{INSTAFIX_HOST}{path_or_url}")


def make_filename(url: str, kind: MediaKind) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix
    if not suffix:
        suffix = ".mp4" if kind == MediaKind.VIDEO else ".jpg"
    return f"instagram_media{suffix}"
