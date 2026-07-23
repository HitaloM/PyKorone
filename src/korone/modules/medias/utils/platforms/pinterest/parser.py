import html
from typing import Any
from urllib.parse import urlparse

import orjson

from korone.modules.medias.utils.parsing import coerce_int, coerce_str, dict_list, dict_or_empty
from korone.modules.medias.utils.types import MediaKind, MediaSource

from .constants import (
    POST_ID_PATTERN,
    RELAY_PAYLOAD_PATTERN,
    URL_SHORTENER_ID_PATTERN,
    VIDEO_LIST_KEYS,
    VIDEO_VARIANT_KEYS,
)

_PIN_TEXT_KEYS = ("description", "title", "gridTitle", "closeupUnifiedTitle", "imageLargeUrl")
_PIN_OBJECT_KEYS = ("videos", "images_orig", "pinner", "nativeCreator")


def extract_post_id(url: str) -> str | None:
    match = POST_ID_PATTERN.search(url)
    if not match:
        return None

    return coerce_str(match.group("id"))


def extract_shortener_id(url: str) -> str | None:
    match = URL_SHORTENER_ID_PATTERN.search(url)
    if not match:
        return None

    return coerce_str(match.group("id"))


def build_post_url(post_id: str) -> str:
    return f"https://www.pinterest.com/pin/{post_id}/"


def extract_pin_data(html_content: str) -> dict[str, Any] | None:
    merged: dict[str, Any] = {}

    for match in RELAY_PAYLOAD_PATTERN.finditer(html_content):
        raw_payload = html.unescape(match.group("payload"))
        try:
            payload = orjson.loads(raw_payload)
        except orjson.JSONDecodeError:
            continue

        relay_data = dict_or_empty(dict_or_empty(payload).get("data"))
        for raw_query in relay_data.values():
            query_data = dict_or_empty(dict_or_empty(raw_query).get("data"))
            if query_data:
                _merge_pin_data(merged, query_data)

    return merged or None


def _merge_pin_data(merged: dict[str, Any], candidate: dict[str, Any]) -> None:
    for key in _PIN_TEXT_KEYS:
        if value := coerce_str(candidate.get(key)):
            merged[key] = value

    for key in _PIN_OBJECT_KEYS:
        value = dict_or_empty(candidate.get(key))
        if value:
            merged[key] = value

    candidate_story = dict_or_empty(candidate.get("storyPinData"))
    if _count_story_blocks(candidate_story) > _count_story_blocks(dict_or_empty(merged.get("storyPinData"))):
        merged["storyPinData"] = candidate_story

    candidate_carousel = dict_or_empty(candidate.get("carouselData"))
    if len(dict_list(candidate_carousel.get("carousel_slots"))) > len(
        dict_list(dict_or_empty(merged.get("carouselData")).get("carousel_slots"))
    ):
        merged["carouselData"] = candidate_carousel


def _count_story_blocks(story_data: dict[str, Any]) -> int:
    return sum(len(dict_list(page.get("blocks"))) for page in dict_list(story_data.get("pages")))


def extract_media_sources(pin_data: dict[str, Any]) -> list[MediaSource]:
    extractors = (
        _extract_story_sources,
        _extract_carousel_sources,
        _extract_single_video_sources,
        _extract_single_image_sources,
    )
    for extractor in extractors:
        sources = _deduplicate_sources(extractor(pin_data))
        if sources:
            return sources

    return []


def _extract_story_sources(pin_data: dict[str, Any]) -> list[MediaSource]:
    story_data = dict_or_empty(pin_data.get("storyPinData"))
    sources: list[MediaSource] = []

    for page in dict_list(story_data.get("pages")):
        for block in dict_list(page.get("blocks")):
            block_type = coerce_str(block.get("__typename"))
            if block_type == "StoryPinVideoBlock":
                source = _extract_story_video_source(dict_or_empty(block.get("videoDataV2")))
            elif block_type == "StoryPinImageBlock":
                source = _extract_story_image_source(dict_or_empty(block.get("imageData")))
            else:
                source = None

            if source:
                sources.append(source)

    return sources


def _extract_story_video_source(video_data: dict[str, Any]) -> MediaSource | None:
    candidates = (
        ("videoList720P", "v720P"),
        ("v_hlsv4_video_list", "vHLSV4"),
        ("videoListMobile", "vHLSV3MOBILE"),
        ("videoList", "vHLSV3MOBILE"),
    )
    for list_key, variant_key in candidates:
        variant = dict_or_empty(dict_or_empty(video_data.get(list_key)).get(variant_key))
        if source := _media_source_from_video_variant(variant):
            return source

    return None


def _extract_story_image_source(image_data: dict[str, Any]) -> MediaSource | None:
    images = dict_or_empty(image_data.get("images"))
    original = dict_or_empty(images.get("orig"))
    image_url = coerce_str(original.get("url"))
    if not image_url:
        return None

    return MediaSource(
        kind=MediaKind.PHOTO,
        url=image_url,
        width=coerce_int(original.get("width")),
        height=coerce_int(original.get("height")),
    )


def _extract_carousel_sources(pin_data: dict[str, Any]) -> list[MediaSource]:
    carousel_data = dict_or_empty(pin_data.get("carouselData"))
    sources: list[MediaSource] = []

    for slot in dict_list(carousel_data.get("carousel_slots")):
        source = _extract_video_source(dict_or_empty(slot.get("videos")))
        if source is None:
            original = dict_or_empty(slot.get("images_orig"))
            image_url = coerce_str(original.get("url"))
            if image_url:
                source = MediaSource(
                    kind=MediaKind.PHOTO,
                    url=image_url,
                    width=coerce_int(original.get("width")),
                    height=coerce_int(original.get("height")),
                )

        if source:
            sources.append(source)

    return sources


def _extract_single_video_sources(pin_data: dict[str, Any]) -> list[MediaSource]:
    source = _extract_video_source(dict_or_empty(pin_data.get("videos")))
    return [source] if source else []


def _extract_video_source(videos: dict[str, Any]) -> MediaSource | None:
    video_lists = [video_list for key in VIDEO_LIST_KEYS if (video_list := dict_or_empty(videos.get(key)))]
    for variant_key in VIDEO_VARIANT_KEYS:
        for video_list in video_lists:
            variant = dict_or_empty(video_list.get(variant_key))
            if source := _media_source_from_video_variant(variant):
                return source

    return None


def _media_source_from_video_variant(variant: dict[str, Any]) -> MediaSource | None:
    video_url = coerce_str(variant.get("url"))
    if not video_url:
        return None

    return MediaSource(
        kind=MediaKind.VIDEO,
        url=video_url,
        thumbnail_url=coerce_str(variant.get("thumbnail")),
        duration=_duration_seconds(variant.get("duration")),
        width=coerce_int(variant.get("width")),
        height=coerce_int(variant.get("height")),
    )


def _duration_seconds(value: object) -> int | None:
    duration_ms = coerce_int(value)
    if duration_ms is None or duration_ms <= 0:
        return None

    return max(1, round(duration_ms / 1000))


def _extract_single_image_sources(pin_data: dict[str, Any]) -> list[MediaSource]:
    original = dict_or_empty(pin_data.get("images_orig"))
    image_url = coerce_str(original.get("url")) or coerce_str(pin_data.get("imageLargeUrl"))
    if not image_url:
        return []

    return [
        MediaSource(
            kind=MediaKind.PHOTO,
            url=image_url,
            width=coerce_int(original.get("width")),
            height=coerce_int(original.get("height")),
        )
    ]


def _deduplicate_sources(sources: list[MediaSource]) -> list[MediaSource]:
    deduplicated: list[MediaSource] = []
    seen: set[str] = set()

    for source in sources:
        if source.url in seen:
            continue
        seen.add(source.url)
        deduplicated.append(source)

    return deduplicated


def extract_author(pin_data: dict[str, Any]) -> str:
    pinner = dict_or_empty(pin_data.get("pinner"))
    native_creator = dict_or_empty(pin_data.get("nativeCreator"))
    return coerce_str(pinner.get("username")) or coerce_str(native_creator.get("username")) or ""


def extract_text(pin_data: dict[str, Any]) -> str:
    title = (
        coerce_str(pin_data.get("closeupUnifiedTitle"))
        or coerce_str(pin_data.get("gridTitle"))
        or coerce_str(pin_data.get("title"))
        or ""
    )
    description = coerce_str(pin_data.get("description")) or ""

    if title and description and title != description:
        return f"{title}\n{description}"
    return title or description


def is_hls_url(url: str) -> bool:
    return urlparse(url).path.casefold().endswith(".m3u8")
