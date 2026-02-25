from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import orjson

from korone.modules.medias.utils.types import MediaKind, MediaSource

from .constants import (
    PLAY_URL_MARKER,
    POST_ID_PATTERN,
    UNIVERSAL_DATA_SCRIPT_PATTERN,
    WEBAPP_DEFAULT_SCOPE_KEY,
    WEBAPP_VIDEO_SCOPE_KEY,
)


@dataclass(frozen=True, slots=True)
class _BitrateCandidate:
    url: str
    codec: str
    data_size: int | None


def ensure_url_scheme(url: str) -> str:
    normalized = url.strip()
    if normalized.startswith(("http://", "https://")):
        return normalized
    return f"https://{normalized.lstrip('/')}"


def extract_post_id(url: str) -> str | None:
    match = POST_ID_PATTERN.search(url)
    if not match:
        return None

    post_id = match.group("id")
    return post_id if post_id.isdigit() else None


def extract_universal_data_payload(html_content: str) -> dict[str, Any] | None:
    match = UNIVERSAL_DATA_SCRIPT_PATTERN.search(html_content)
    if not match:
        return None

    raw_payload = html.unescape(match.group("payload").strip())
    if not raw_payload:
        return None

    try:
        payload = orjson.loads(raw_payload)
    except orjson.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def extract_item_struct(payload: dict[str, Any]) -> dict[str, Any] | None:
    default_scope = payload.get(WEBAPP_DEFAULT_SCOPE_KEY)
    if not isinstance(default_scope, dict):
        return None

    video_scope = default_scope.get(WEBAPP_VIDEO_SCOPE_KEY)
    if not isinstance(video_scope, dict):
        return None

    status_code = coerce_int(video_scope.get("statusCode"))
    if status_code is not None and status_code != 0:
        return None

    item_info = video_scope.get("itemInfo")
    if not isinstance(item_info, dict):
        return None

    item_struct = item_info.get("itemStruct")
    return item_struct if isinstance(item_struct, dict) else None


def extract_media_sources(item_struct: dict[str, Any]) -> list[MediaSource]:
    image_sources = extract_image_sources(item_struct)
    if image_sources:
        return image_sources

    video_source = extract_video_source(item_struct)
    if video_source:
        return [video_source]

    return []


def extract_image_sources(item_struct: dict[str, Any]) -> list[MediaSource]:
    image_post = item_struct.get("imagePost")
    if not isinstance(image_post, dict):
        return []

    images_raw = image_post.get("images")
    if not isinstance(images_raw, list):
        return []

    sources: list[MediaSource] = []
    seen: set[str] = set()

    for image_raw in images_raw:
        if not isinstance(image_raw, dict):
            continue

        image_url_data = image_raw.get("imageURL")
        image_url_map = image_url_data if isinstance(image_url_data, dict) else {}
        image_url = pick_url(image_url_map.get("urlList"))
        if not image_url or image_url in seen:
            continue

        seen.add(image_url)
        sources.append(
            MediaSource(
                kind=MediaKind.PHOTO,
                url=image_url,
                width=coerce_int(image_raw.get("imageWidth")),
                height=coerce_int(image_raw.get("imageHeight")),
            )
        )

    return sources


def extract_video_source(item_struct: dict[str, Any]) -> MediaSource | None:
    video_raw = item_struct.get("video")
    video = video_raw if isinstance(video_raw, dict) else {}

    play_url = pick_video_url(video)
    if not play_url:
        return None

    return MediaSource(
        kind=MediaKind.VIDEO,
        url=play_url,
        thumbnail_url=pick_nonempty_str(video.get("originCover"))
        or pick_nonempty_str(video.get("cover"))
        or pick_nonempty_str(video.get("dynamicCover")),
        duration=coerce_int(video.get("duration")),
        width=coerce_int(video.get("width")),
        height=coerce_int(video.get("height")),
    )


def pick_video_url(video: dict[str, Any]) -> str | None:
    bitrate_info = video.get("bitrateInfo")
    candidates = (
        [candidate for candidate in map(build_bitrate_candidate, bitrate_info) if candidate]
        if isinstance(bitrate_info, list)
        else []
    )

    chosen_candidate = select_bitrate_candidate(candidates)
    if chosen_candidate:
        return chosen_candidate.url

    play_struct_raw = video.get("PlayAddrStruct")
    play_struct = play_struct_raw if isinstance(play_struct_raw, dict) else {}
    play_url = pick_url(play_struct.get("UrlList"), preferred_substring=PLAY_URL_MARKER)
    if play_url:
        return play_url

    return pick_nonempty_str(video.get("playAddr"))


def build_bitrate_candidate(entry: object) -> _BitrateCandidate | None:
    if not isinstance(entry, dict):
        return None

    play_addr_raw = entry.get("PlayAddr")
    play_addr = play_addr_raw if isinstance(play_addr_raw, dict) else {}
    play_url = pick_url(play_addr.get("UrlList"), preferred_substring=PLAY_URL_MARKER)
    if not play_url:
        return None

    codec = pick_nonempty_str(entry.get("CodecType")) or ""
    data_size = coerce_int(play_addr.get("DataSize"))
    return _BitrateCandidate(
        url=play_url, codec=codec.lower(), data_size=data_size if data_size and data_size > 0 else None
    )


def select_bitrate_candidate(candidates: list[_BitrateCandidate]) -> _BitrateCandidate | None:
    if not candidates:
        return None

    return min(candidates, key=lambda candidate: (candidate_priority(candidate), -(candidate.data_size or 0)))


def candidate_priority(candidate: _BitrateCandidate) -> int:
    is_h265 = "h265" in candidate.codec

    if is_h265:
        return 0
    return 1


def pick_url(url_list: object, *, preferred_substring: str | None = None) -> str | None:
    if not isinstance(url_list, list):
        return None

    candidates = [url.strip() for url in url_list if isinstance(url, str) and url.strip()]
    if not candidates:
        return None

    if preferred_substring:
        for url in candidates:
            if preferred_substring in url:
                return url

    return candidates[0]


def extract_author(item_struct: dict[str, Any]) -> tuple[str, str]:
    author_raw = item_struct.get("author")
    author = author_raw if isinstance(author_raw, dict) else {}

    author_name = pick_nonempty_str(author.get("nickname")) or ""
    author_handle = (pick_nonempty_str(author.get("uniqueId")) or "").lstrip("@")
    if not author_handle and author_name:
        author_handle = author_name.lstrip("@")

    return author_name, author_handle


def extract_text(item_struct: dict[str, Any]) -> str:
    return pick_nonempty_str(item_struct.get("desc")) or ""


def build_post_url(item_struct: dict[str, Any], fallback_url: str) -> str:
    post_id = pick_nonempty_str(item_struct.get("id"))
    _, author_handle = extract_author(item_struct)
    if post_id and author_handle:
        post_kind = "photo" if is_carousel_post(item_struct) else "video"
        return f"https://www.tiktok.com/@{quote(author_handle)}/{post_kind}/{quote(post_id)}"
    return fallback_url


def is_carousel_post(item_struct: dict[str, Any]) -> bool:
    image_post = item_struct.get("imagePost")
    if not isinstance(image_post, dict):
        return False
    images = image_post.get("images")
    return isinstance(images, list) and bool(images)


def pick_nonempty_str(value: object) -> str | None:
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
