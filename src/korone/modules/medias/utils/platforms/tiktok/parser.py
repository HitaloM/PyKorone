from __future__ import annotations

from typing import Any
from urllib.parse import quote

from korone.modules.medias.utils.types import MediaKind, MediaSource

from .constants import POST_ID_PATTERN, TIKTOK_IMAGE_AWEME_TYPES


def ensure_url_scheme(url: str) -> str:
    if url.startswith(("http://", "https://")):
        return url
    return f"https://{url.lstrip('/')}"


def extract_post_id(url: str) -> str | None:
    match = POST_ID_PATTERN.search(url)
    if not match:
        return None

    post_id = match.group("id")
    return post_id if post_id.isdigit() else None


def extract_first_aweme(payload: dict[str, Any], post_id: str) -> dict[str, Any] | None:
    aweme_list_raw = payload.get("aweme_list")
    if not isinstance(aweme_list_raw, list) or not aweme_list_raw:
        return None

    first_aweme = aweme_list_raw[0]
    if not isinstance(first_aweme, dict):
        return None

    aweme_id_raw = first_aweme.get("aweme_id")
    aweme_id = str(aweme_id_raw).strip() if aweme_id_raw is not None else ""
    if aweme_id != post_id:
        return None

    return first_aweme


def extract_media_sources(aweme: dict[str, Any]) -> list[MediaSource]:
    aweme_type = coerce_int(aweme.get("aweme_type"))
    if aweme_type in TIKTOK_IMAGE_AWEME_TYPES:
        image_sources = extract_image_sources(aweme)
        if image_sources:
            return image_sources

    video_sources = extract_video_sources(aweme)
    if video_sources:
        return video_sources

    return extract_image_sources(aweme)


def extract_image_sources(aweme: dict[str, Any]) -> list[MediaSource]:
    image_post_info = aweme.get("image_post_info")
    if not isinstance(image_post_info, dict):
        return []

    images_raw = image_post_info.get("images")
    if not isinstance(images_raw, list):
        return []

    sources: list[MediaSource] = []
    seen: set[str] = set()
    for image_raw in images_raw:
        if not isinstance(image_raw, dict):
            continue

        display_image = image_raw.get("display_image")
        display = display_image if isinstance(display_image, dict) else {}
        thumbnail_image = image_raw.get("thumbnail")
        thumbnail = thumbnail_image if isinstance(thumbnail_image, dict) else {}

        image_url = pick_url(display.get("url_list"), preferred_index=1)
        if not image_url or image_url in seen:
            continue

        seen.add(image_url)
        thumbnail_url = pick_url(thumbnail.get("url_list"), preferred_index=0)
        sources.append(MediaSource(kind=MediaKind.PHOTO, url=image_url, thumbnail_url=thumbnail_url))

    return sources


def extract_video_sources(aweme: dict[str, Any]) -> list[MediaSource]:
    video_raw = aweme.get("video")
    video = video_raw if isinstance(video_raw, dict) else {}

    play_addr_raw = video.get("play_addr")
    play_addr = play_addr_raw if isinstance(play_addr_raw, dict) else {}
    cover_raw = video.get("cover")
    cover = cover_raw if isinstance(cover_raw, dict) else {}

    video_url = pick_url(play_addr.get("url_list"), preferred_index=0)
    if not video_url:
        return []

    duration_ms = coerce_int(video.get("duration"))
    duration = duration_ms // 1000 if isinstance(duration_ms, int) and duration_ms > 0 else None

    width = coerce_int(play_addr.get("width")) or coerce_int(video.get("width"))
    height = coerce_int(play_addr.get("height")) or coerce_int(video.get("height"))

    return [
        MediaSource(
            kind=MediaKind.VIDEO,
            url=video_url,
            thumbnail_url=pick_url(cover.get("url_list"), preferred_index=0),
            duration=duration,
            width=width,
            height=height,
        )
    ]


def pick_url(url_list: object, *, preferred_index: int) -> str | None:
    if not isinstance(url_list, list):
        return None

    candidates = [value.strip() for value in url_list if isinstance(value, str) and value.strip()]
    if not candidates:
        return None

    if 0 <= preferred_index < len(candidates):
        return candidates[preferred_index]
    return candidates[0]


def extract_author(aweme: dict[str, Any]) -> tuple[str, str]:
    author_raw = aweme.get("author")
    author = author_raw if isinstance(author_raw, dict) else {}

    nickname = author.get("nickname")
    unique_id = author.get("unique_id")

    author_name = str(nickname).strip() if isinstance(nickname, str) else ""
    author_handle = str(unique_id).strip().lstrip("@") if isinstance(unique_id, str) else ""
    if not author_handle and author_name:
        author_handle = author_name.lstrip("@")

    return author_name, author_handle


def extract_text(aweme: dict[str, Any]) -> str:
    description = aweme.get("desc")
    return str(description).strip() if isinstance(description, str) else ""


def extract_post_url(aweme: dict[str, Any], author_handle: str, post_id: str, fallback_url: str) -> str:
    share_url = aweme.get("share_url")
    if isinstance(share_url, str) and share_url.startswith(("https://", "http://")):
        return share_url

    if author_handle:
        return f"https://www.tiktok.com/@{quote(author_handle)}/video/{quote(post_id)}"

    return fallback_url


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
