import html
from urllib.parse import urlsplit, urlunsplit

from lxml import html as lxml_html

from korone.modules.medias.utils.parsing import coerce_str, ensure_url_scheme
from korone.modules.medias.utils.types import MediaKind

from .constants import INSTAFIX_HOST, INSTAGRAM_HOST, POST_PATTERN
from .types import InstaData, InstaMedia


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
        elif prop == "og:image":
            image_url = build_instafix_media_url(content)
            if not media_url:
                media_type = "photo"
                media_url = image_url

    if not media_url:
        return None

    return InstaData(
        media=(
            InstaMedia(
                url=media_url,
                kind=MediaKind.VIDEO if media_type == "video" else MediaKind.PHOTO,
            ),
        ),
        username=username,
        description=description,
    )


def build_instafix_media_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        return ensure_url_scheme(path_or_url)
    return ensure_url_scheme(f"{INSTAFIX_HOST}{path_or_url}")


def extract_post_id(url: str) -> str | None:
    match = POST_PATTERN.search(url)
    return match.group("post_id") if match else None


def build_offload_url(instafix_url: str, post_id: str, media_index: int, *, thumbnail: bool = False) -> str:
    parsed = urlsplit(ensure_url_scheme(instafix_url))
    query = "thumbnail=1" if thumbnail else ""
    return urlunsplit(parsed._replace(path=f"/offload/{post_id}/{media_index}", query=query, fragment=""))
