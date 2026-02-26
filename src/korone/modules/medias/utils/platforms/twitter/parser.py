from __future__ import annotations

import re
from typing import Any, cast
from urllib.parse import urlparse

from korone.modules.medias.utils.types import MediaKind, MediaSource

_STATUS_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:x\.com|(?:www\.|mobile\.)?twitter\.com)/"
    r"(?:i/(?:web/)?|(?P<handle>[A-Za-z0-9_]{1,15})/)?status/(?P<id>\d+)",
    re.IGNORECASE,
)
_VIDEO_MEDIA_TYPES = {"video", "gif", "animated_gif"}


def extract_status_id_and_handle(url: str) -> tuple[str | None, str | None]:
    match = _STATUS_URL_PATTERN.search(url)
    if not match:
        return None, None

    status_id = match.group("id")
    handle = normalize_handle(match.group("handle"))
    return status_id, handle


def normalize_handle(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    handle = value.strip().lstrip("@")
    if not handle:
        return None

    normalized = handle.lower()
    if normalized in {"i", "web"}:
        return None
    return handle


def extract_status_code(data: dict[str, Any]) -> int | None:
    return coerce_int(data.get("code"))


def extract_status_message(data: dict[str, Any]) -> str:
    message = data.get("message")
    if isinstance(message, str):
        return message
    return ""


def extract_tweet_payload(data: dict[str, Any]) -> dict[str, Any] | None:
    status_code = extract_status_code(data)
    if status_code is not None and status_code != 200:
        return None

    if "tweet" in data and isinstance(data["tweet"], dict):
        return data["tweet"]
    if "data" in data and isinstance(data["data"], dict):
        return data["data"]
    if "tweet" not in data and "data" not in data:
        return data
    return None


def extract_author(tweet: dict[str, Any]) -> tuple[str, str]:
    author = tweet.get("author") or tweet.get("user") or {}
    author_name = author.get("name") or tweet.get("author_name") or tweet.get("user_name") or ""
    author_handle = normalize_handle(
        author.get("screen_name")
        or author.get("username")
        or author.get("handle")
        or tweet.get("author_handle")
        or tweet.get("user_screen_name")
    )
    return str(author_name), author_handle or ""


def extract_text(tweet: dict[str, Any]) -> str:
    text = tweet.get("text") or tweet.get("translation") or tweet.get("full_text") or tweet.get("content") or ""
    return str(text)


def extract_post_url(tweet: dict[str, Any], status_id: str, handle: str | None, fallback: str) -> str:
    url = tweet.get("url") or tweet.get("tweet_url") or ""
    if url:
        return str(url)
    if handle:
        return f"https://x.com/{handle}/status/{status_id}"
    return fallback


def extract_media_sources(tweet: dict[str, Any]) -> list[MediaSource]:
    media = tweet.get("media")
    if not isinstance(media, dict):
        media = {}

    sources: list[MediaSource] = []
    seen: set[str] = set()

    def _add(
        kind: MediaKind,
        url: str,
        *,
        thumbnail_url: str | None = None,
        duration: int | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        if not url or url in seen:
            return
        seen.add(url)
        sources.append(
            MediaSource(kind=kind, url=url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)
        )

    def _extract_metadata(item: dict[str, Any]) -> tuple[str | None, int | None, int | None, int | None]:
        thumbnail_url = item.get("thumbnail_url") or item.get("thumb") or item.get("preview_image_url")
        return (
            str(thumbnail_url) if isinstance(thumbnail_url, str) else None,
            coerce_int(item.get("duration")),
            coerce_int(item.get("width")),
            coerce_int(item.get("height")),
        )

    for photo in ensure_list(media.get("photos")) + ensure_list(media.get("images")):
        if url := coerce_url(photo.get("url") or photo.get("src") or photo.get("source")):
            thumbnail_url, duration, width, height = _extract_metadata(photo)
            _add(MediaKind.PHOTO, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    for video in ensure_list(media.get("videos")) + ensure_list(media.get("video")):
        url = pick_video_url(video)
        if url:
            thumbnail_url, duration, width, height = _extract_metadata(video)
            _add(MediaKind.VIDEO, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    for item in ensure_list(media.get("all")):
        kind = resolve_kind(item)
        url = pick_video_url(item) if kind == MediaKind.VIDEO else coerce_url(item.get("url") or item.get("src"))
        if not url:
            url = coerce_url(item.get("source"))
        if not url:
            continue

        thumbnail_url, duration, width, height = _extract_metadata(item)
        _add(kind, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    if not sources:
        media_url = coerce_url(tweet.get("media_url") or tweet.get("media_url_https"))
        if media_url:
            _add(MediaKind.PHOTO, media_url)

    return sources


def pick_video_url(video: dict[str, Any]) -> str | None:
    variants = ensure_list(video.get("variants"))
    if best_variant := pick_best_variant(variants):
        return best_variant

    direct_url = coerce_url(video.get("url") or video.get("src") or video.get("source"))
    if not direct_url:
        return None

    format_hint = video.get("format") or video.get("content_type")
    if looks_like_hls(direct_url, format_hint) or not looks_like_mp4(direct_url, format_hint):
        return None
    return direct_url


def pick_best_variant(variants: list[dict[str, Any]]) -> str | None:
    best_mp4_url: str | None = None
    best_mp4_bitrate = -1

    for variant in variants:
        if not isinstance(variant, dict):
            continue

        url = coerce_url(variant.get("url"))
        if not url:
            continue

        format_hint = variant.get("content_type") or variant.get("format")
        if looks_like_hls(url, format_hint) or not looks_like_mp4(url, format_hint):
            continue

        bitrate = coerce_int(variant.get("bitrate")) or -1
        if bitrate <= best_mp4_bitrate:
            continue

        best_mp4_bitrate = bitrate
        best_mp4_url = url

    return best_mp4_url


def looks_like_hls(url: str, format_hint: object) -> bool:
    lowered_url = url.lower()
    if ".m3u8" in lowered_url:
        return True

    parsed = urlparse(url)
    if parsed.path.lower().endswith(".m3u8"):
        return True

    if isinstance(format_hint, str):
        lowered_format = format_hint.lower()
        return "mpegurl" in lowered_format or "m3u8" in lowered_format

    return False


def looks_like_mp4(url: str, format_hint: object) -> bool:
    parsed = urlparse(url)
    if parsed.path.lower().endswith(".mp4"):
        return True

    if isinstance(format_hint, str):
        lowered_format = format_hint.lower()
        return "video/mp4" in lowered_format or lowered_format == "mp4"

    return False


def resolve_kind(item: dict[str, Any]) -> MediaKind:
    media_type = item.get("type")
    if isinstance(media_type, str) and media_type.lower() in _VIDEO_MEDIA_TYPES:
        return MediaKind.VIDEO
    return MediaKind.PHOTO


def ensure_list(value: object) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [cast("dict[str, Any]", item) for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [cast("dict[str, Any]", value)]
    return []


def coerce_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    url = value.strip()
    if not url:
        return None
    return url


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
