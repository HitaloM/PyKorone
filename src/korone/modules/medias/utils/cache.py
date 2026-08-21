from typing import TYPE_CHECKING, Any, NotRequired, TypedDict

from korone.modules.utils_.file_id_cache import (
    delete_cached_file_payload,
    get_cached_file_payload,
    make_file_id_cache_key,
    set_cached_file_payload,
)

from .types import MediaItem, MediaKind, MediaPost
from .url import normalize_media_url

if TYPE_CHECKING:
    from .provider_base import MediaProvider

POST_CACHE_NAMESPACE = "media-post"
MEDIA_SOURCE_CACHE_NAMESPACE = "media-source"


class MediaCacheEntryPayload(TypedDict, total=False):
    kind: str
    file_id: str
    source_url: str
    duration: int
    width: int
    height: int


class PostCachePayload(TypedDict):
    author_name: str
    author_handle: str
    text: str
    url: str
    website: str
    media: list[MediaCacheEntryPayload]
    quote_text: NotRequired[str]
    quote_author_name: NotRequired[str]
    quote_author_handle: NotRequired[str]


def post_cache_key(url: str) -> str:
    return make_file_id_cache_key(POST_CACHE_NAMESPACE, url)


def media_source_cache_key(source_url: str) -> str:
    cache_identifier = normalize_media_url(source_url) or source_url.strip() or source_url
    return make_file_id_cache_key(MEDIA_SOURCE_CACHE_NAMESPACE, cache_identifier)


def serialize_media_entry(media: MediaItem, file_id: str) -> MediaCacheEntryPayload:
    payload: MediaCacheEntryPayload = {"kind": media.kind.value, "file_id": file_id, "source_url": media.source_url}
    for field in ("duration", "width", "height"):
        if (value := getattr(media, field)) is not None:
            payload[field] = value
    return payload


def deserialize_media_entry(payload: dict[str, Any], index: int) -> MediaItem | None:
    match payload:
        case {"kind": str() as kind_raw, "file_id": str() as file_id, **rest} if file_id:
            try:
                kind = MediaKind(kind_raw)
            except ValueError:
                return None
        case _:
            return None

    source_url = rest.get("source_url")
    if not isinstance(source_url, str) or not source_url:
        source_url = f"cached://{index}"

    return MediaItem(
        kind=kind,
        file=file_id,
        filename=f"cached_media_{index}",
        source_url=source_url,
        duration=_cached_int(rest.get("duration")),
        width=_cached_int(rest.get("width")),
        height=_cached_int(rest.get("height")),
    )


def serialize_post(post: MediaPost, media: list[MediaCacheEntryPayload]) -> PostCachePayload:
    payload: PostCachePayload = {
        "author_name": post.author_name,
        "author_handle": post.author_handle,
        "text": post.text,
        "url": post.url,
        "website": post.website,
        "media": media,
    }
    for field in ("quote_text", "quote_author_name", "quote_author_handle"):
        if value := getattr(post, field):
            payload[field] = value
    return payload


def deserialize_post(payload: dict[str, Any], provider: type[MediaProvider]) -> MediaPost | None:
    match payload:
        case {"media": list(raw_media), "url": str() as url, "website": str() as website, **rest} if url and website:
            pass
        case _:
            return None

    media = []
    for index, entry in enumerate(raw_media, start=1):
        if not isinstance(entry, dict) or (item := deserialize_media_entry(entry, index)) is None:
            return None
        media.append(item)
    if not media:
        return None

    author_name = rest.get("author_name")
    author_handle = rest.get("author_handle")
    text = rest.get("text")
    quote_text = rest.get("quote_text")
    quote_author_name = rest.get("quote_author_name")
    quote_author_handle = rest.get("quote_author_handle")
    return MediaPost(
        author_name=author_name if isinstance(author_name, str) and author_name else provider.name,
        author_handle=(author_handle if isinstance(author_handle, str) and author_handle else provider.name.casefold()),
        text=text if isinstance(text, str) else "",
        url=url,
        website=website,
        media=media,
        quote_text=quote_text if isinstance(quote_text, str) and quote_text else None,
        quote_author_name=quote_author_name if isinstance(quote_author_name, str) and quote_author_name else None,
        quote_author_handle=(
            quote_author_handle if isinstance(quote_author_handle, str) and quote_author_handle else None
        ),
    )


async def get_cached_post(provider: type[MediaProvider], source_url: str) -> tuple[str, MediaPost] | None:
    for candidate_url in _post_cache_candidates(source_url):
        key = post_cache_key(candidate_url)
        cached_payload = await get_cached_file_payload(key)
        if not cached_payload:
            continue
        if cached_post := deserialize_post(cached_payload, provider):
            return candidate_url, cached_post
        await delete_cached_file_payload(key)
    return None


async def delete_cached_post(*urls: str) -> None:
    for candidate_url in _post_cache_candidates(*urls):
        await delete_cached_file_payload(post_cache_key(candidate_url))


async def set_cached_post(source_url: str, post: MediaPost, media: list[MediaCacheEntryPayload]) -> None:
    if not media:
        return
    payload = serialize_post(post, media)
    for candidate_url in _post_cache_candidates(source_url, post.url):
        await set_cached_file_payload(post_cache_key(candidate_url), payload)


async def cache_media_file_id(source_url: str, file_id: str) -> None:
    await set_cached_file_payload(media_source_cache_key(source_url), {"file_id": file_id})


def _post_cache_candidates(*urls: str) -> set[str]:
    return {candidate for url in urls if (candidate := url.strip())}


def _cached_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
