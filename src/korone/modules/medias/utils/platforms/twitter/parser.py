from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from korone.modules.medias.utils.parsing import coerce_int, coerce_str, dict_list, dict_or_empty
from korone.modules.medias.utils.types import MediaKind, MediaSource

if TYPE_CHECKING:
    from collections.abc import Iterator

_STATUS_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:x\.com|(?:www\.|mobile\.)?twitter\.com)/"
    r"(?:i/(?:web/)?|(?P<handle>[A-Za-z0-9_]{1,15})/)?status/(?P<id>\d+)",
    re.IGNORECASE,
)
_VIDEO_MEDIA_TYPES = {"video", "gif", "animated_gif"}
_TRAILING_TCO_LINK_PATTERN = re.compile(r"(?:\s+)?https://t\.co/[A-Za-z0-9]+(?:\u2026)?\s*$", re.IGNORECASE)


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
    return coerce_str(data.get("message")) or ""


def extract_tweet_payload(data: dict[str, Any]) -> dict[str, Any] | None:
    status_code = extract_status_code(data)
    if status_code is not None and status_code != 200:
        return None

    status = dict_or_empty(data.get("status"))
    if status:
        return status

    return None


def extract_author(tweet: dict[str, Any]) -> tuple[str, str]:
    author = dict_or_empty(tweet.get("author"))
    author_name = coerce_str(author.get("name")) or ""
    author_handle = normalize_handle(author.get("screen_name"))
    return author_name, author_handle or ""


def extract_text(tweet: dict[str, Any]) -> str:
    return _extract_status_text(tweet)


def extract_quote(tweet: dict[str, Any]) -> tuple[str | None, str | None, str | None] | None:
    quoted_tweet = extract_quoted_tweet(tweet)
    if not quoted_tweet:
        return None

    normalized_quote_text = _extract_status_text(quoted_tweet)

    quote_author_name, quote_author_handle = extract_author(quoted_tweet)
    normalized_quote_author_name = quote_author_name or None
    normalized_quote_author_handle = quote_author_handle or None

    if not normalized_quote_text and not normalized_quote_author_name and not normalized_quote_author_handle:
        return None

    return normalized_quote_text or None, normalized_quote_author_name, normalized_quote_author_handle


def extract_post_url(tweet: dict[str, Any], status_id: str, handle: str | None, fallback: str) -> str:
    url = coerce_str(tweet.get("url") or tweet.get("tweet_url")) or ""
    if url:
        return url
    if handle:
        return f"https://x.com/{handle}/status/{status_id}"
    return fallback


def extract_media_sources(tweet: dict[str, Any]) -> list[MediaSource]:
    media = _extract_fxtwitter_media(tweet)

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

    for photo in iter_media_dicts(media.get("photos"), media.get("images")):
        if url := coerce_url(photo.get("url") or photo.get("src") or photo.get("source")):
            thumbnail_url, duration, width, height = _extract_media_metadata(photo)
            _add(MediaKind.PHOTO, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    for video in iter_media_dicts(media.get("videos"), media.get("video")):
        url = pick_video_url(video)
        if url:
            thumbnail_url, duration, width, height = _extract_media_metadata(video)
            _add(MediaKind.VIDEO, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    for item in iter_media_dicts(media.get("all")):
        kind = resolve_kind(item)
        url = pick_video_url(item) if kind == MediaKind.VIDEO else coerce_url(item.get("url") or item.get("src"))
        if not url:
            url = coerce_url(item.get("source"))
        if not url:
            continue

        thumbnail_url, duration, width, height = _extract_media_metadata(item)
        _add(kind, url, thumbnail_url=thumbnail_url, duration=duration, width=width, height=height)

    return sources


def pick_video_url(video: dict[str, Any]) -> str | None:
    variants = dict_list(video.get("formats"))
    if not variants:
        variants = dict_list(video.get("variants"))

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


def _extract_status_text(tweet: dict[str, Any]) -> str:
    raw_text = dict_or_empty(tweet.get("raw_text"))
    translation = dict_or_empty(tweet.get("translation"))

    candidates = (coerce_str(tweet.get("text")), coerce_str(raw_text.get("text")), coerce_str(translation.get("text")))

    for candidate in candidates:
        if not candidate:
            continue

        normalized = _strip_trailing_tco_link(candidate).strip()
        if normalized:
            return normalized

    return ""


def extract_quoted_tweet(tweet: dict[str, Any]) -> dict[str, Any] | None:
    quote = dict_or_empty(tweet.get("quote"))
    if quote:
        return quote

    return None


def iter_media_dicts(*values: object) -> Iterator[dict[str, Any]]:
    for value in values:
        yield from dict_list(value)


def coerce_url(value: object) -> str | None:
    return coerce_str(value)


def _extract_media_metadata(item: dict[str, Any]) -> tuple[str | None, int | None, int | None, int | None]:
    original_info = dict_or_empty(item.get("original_info"))
    thumbnail_url = coerce_str(
        item.get("thumbnail_url")
        or item.get("thumb")
        or item.get("preview_image_url")
        or item.get("media_url_https")
        or item.get("media_url")
    )
    duration = coerce_int(item.get("duration"))
    width = coerce_int(item.get("width") or original_info.get("width"))
    height = coerce_int(item.get("height") or original_info.get("height"))
    return thumbnail_url, duration, width, height


def _extract_fxtwitter_media(tweet: dict[str, Any]) -> dict[str, Any]:
    media = dict_or_empty(tweet.get("media"))
    if media:
        return media

    quoted_tweet = extract_quoted_tweet(tweet)
    if not quoted_tweet:
        return {}

    return dict_or_empty(quoted_tweet.get("media"))


def _strip_trailing_tco_link(text: str) -> str:
    return _TRAILING_TCO_LINK_PATTERN.sub("", text)
