from __future__ import annotations

import base64
import binascii
import json

import aiohttp

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient

from .types import HifiTrack, HifiTrackStream

logger = get_logger(__name__)

HIFI_API_BASE_URLS = (
    "https://wolf.qqdl.site",
    "https://maus.qqdl.site",
    "https://vogel.qqdl.site",
    "https://katze.qqdl.site",
    "https://hund.qqdl.site",
)
HIFI_API_TIMEOUT_SECONDS = 20
HIFI_DOWNLOAD_TIMEOUT_SECONDS = 120
QUALITY_FALLBACK_ORDER = ("LOSSLESS", "HIGH", "LOW")


class HifiAPIError(Exception):
    def __init__(self, message: str = "HiFi API error") -> None:
        super().__init__(message)


class HifiRequestFailedError(HifiAPIError):
    __slots__ = ("status_code",)

    def __init__(self, status_code: int) -> None:
        super().__init__(f"HiFi API request failed with status {status_code}")
        self.status_code = status_code


class HifiPayloadError(HifiAPIError):
    def __init__(self, message: str = "HiFi API returned an invalid payload") -> None:
        super().__init__(message)


class HifiStreamUnavailableError(HifiAPIError):
    def __init__(self, message: str = "HiFi audio stream is unavailable") -> None:
        super().__init__(message)


class HifiTrackTooLargeError(HifiAPIError):
    def __init__(self, message: str = "HiFi track is too large for Telegram") -> None:
        super().__init__(message)


def _build_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _pick_artist(item: dict[str, object]) -> str:
    main_artist = item.get("artist")
    if isinstance(main_artist, dict):
        main_name = main_artist.get("name")
        if isinstance(main_name, str) and main_name.strip():
            return main_name.strip()

    artists = item.get("artists")
    if isinstance(artists, list):
        for artist in artists:
            if not isinstance(artist, dict):
                continue
            name = artist.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()

    return "Unknown artist"


def _pick_album(item: dict[str, object]) -> str | None:
    album = item.get("album")
    if not isinstance(album, dict):
        return None

    name = album.get("title")
    if isinstance(name, str) and name.strip():
        return name.strip()

    return None


def _pick_album_cover_id(item: dict[str, object]) -> str | None:
    album = item.get("album")
    if not isinstance(album, dict):
        return None

    cover_id = album.get("cover")
    if isinstance(cover_id, str) and cover_id.strip():
        return cover_id.strip()

    return None


def _parse_track_item(item: dict[str, object]) -> HifiTrack | None:
    track_id = _as_int(item.get("id"))
    title = item.get("title")
    if track_id is None or not isinstance(title, str):
        return None

    clean_title = title.strip()
    if not clean_title:
        return None

    explicit_value = item.get("explicit")
    explicit = explicit_value if isinstance(explicit_value, bool) else False

    quality_value = item.get("audioQuality")
    quality = quality_value if isinstance(quality_value, str) and quality_value else None

    return HifiTrack(
        id=track_id,
        title=clean_title,
        artist=_pick_artist(item),
        album=_pick_album(item),
        album_cover_id=_pick_album_cover_id(item),
        duration=_as_int(item.get("duration")),
        explicit=explicit,
        audio_quality=quality,
    )


def _decode_manifest(manifest: str) -> str:
    padding = "=" * (-len(manifest) % 4)
    decoded = base64.b64decode(f"{manifest}{padding}")
    return decoded.decode("utf-8")


def _extract_stream(data: dict[str, object]) -> tuple[str | None, str | None, str | None]:
    manifest_type = data.get("manifestMimeType")
    manifest = data.get("manifest")
    if manifest_type != "application/vnd.tidal.bts" or not isinstance(manifest, str):
        return None, None, None

    try:
        manifest_payload = _decode_manifest(manifest)
        parsed_manifest = json.loads(manifest_payload)
    except binascii.Error, json.JSONDecodeError, UnicodeDecodeError:
        return None, None, None

    if not isinstance(parsed_manifest, dict):
        return None, None, None

    urls = parsed_manifest.get("urls")
    if not isinstance(urls, list):
        return None, None, None

    stream_url = next((url for url in urls if isinstance(url, str) and url), None)
    if stream_url is None:
        return None, None, None

    mime_type = parsed_manifest.get("mimeType")
    codecs = parsed_manifest.get("codecs")

    return (
        stream_url,
        mime_type if isinstance(mime_type, str) and mime_type else None,
        codecs if isinstance(codecs, str) and codecs else None,
    )


def _quality_order(preferred_quality: str) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    for quality in (preferred_quality, *QUALITY_FALLBACK_ORDER):
        normalized = quality.strip().upper()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)

    return ordered


async def _request_json(path: str, *, params: dict[str, str | int]) -> dict[str, object]:
    timeout = aiohttp.ClientTimeout(total=HIFI_API_TIMEOUT_SECONDS)
    session = await HTTPClient.get_session()
    last_error: HifiAPIError | None = None

    for base_url in HIFI_API_BASE_URLS:
        url = _build_url(base_url, path)

        try:
            async with session.get(url, params=params, timeout=timeout) as response:
                if response.status != 200:
                    await logger.adebug("[HiFi] Unexpected status", status=response.status, url=url)
                    last_error = HifiRequestFailedError(response.status)
                    continue

                try:
                    payload = await response.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError) as exc:
                    last_error = HifiPayloadError("HiFi API returned invalid JSON")
                    await logger.adebug("[HiFi] Invalid payload", error=str(exc), url=url)
                    continue

        except TimeoutError as exc:
            last_error = HifiAPIError("HiFi API request timed out")
            await logger.aerror("[HiFi] Request timed out", error=str(exc), url=url)
            continue
        except aiohttp.ClientError as exc:
            last_error = HifiAPIError("HiFi API request failed")
            await logger.aerror("[HiFi] Request failed", error=str(exc), url=url)
            continue

        if not isinstance(payload, dict):
            last_error = HifiPayloadError("HiFi API returned an unexpected payload shape")
            await logger.adebug("[HiFi] Invalid payload shape", url=url)
            continue

        return payload

    if last_error is not None:
        raise last_error

    msg = "HiFi API request failed on all upstreams"
    raise HifiAPIError(msg)


async def search_tracks(query: str) -> list[HifiTrack]:
    payload = await _request_json("/search/", params={"s": query})
    data = payload.get("data")
    if not isinstance(data, dict):
        return []

    items = data.get("items")
    if not isinstance(items, list):
        return []

    tracks: list[HifiTrack] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        track = _parse_track_item(item)
        if track:
            tracks.append(track)

    return tracks


async def get_track_stream(track_id: int, *, preferred_quality: str = "LOSSLESS") -> HifiTrackStream:
    last_error: HifiAPIError | None = None

    for quality in _quality_order(preferred_quality):
        try:
            payload = await _request_json("/track/", params={"id": track_id, "quality": quality})
        except HifiRequestFailedError as exc:
            last_error = exc
            continue

        data = payload.get("data")
        if not isinstance(data, dict):
            continue

        stream_url, mime_type, codec = _extract_stream(data)
        if not stream_url:
            continue

        quality_value = data.get("audioQuality")
        resolved_quality = quality_value if isinstance(quality_value, str) and quality_value else quality

        return HifiTrackStream(
            url=stream_url, audio_quality=resolved_quality, mime_type=mime_type, codec=codec, requested_quality=quality
        )

    if last_error is not None:
        msg = f"No stream available for track id {track_id}"
        raise HifiStreamUnavailableError(msg) from last_error

    msg = f"No stream available for track id {track_id}"
    raise HifiStreamUnavailableError(msg)


async def download_cover_image(cover_url: str) -> bytes | None:
    timeout = aiohttp.ClientTimeout(total=HIFI_API_TIMEOUT_SECONDS)
    session = await HTTPClient.get_session()

    try:
        async with session.get(cover_url, timeout=timeout) as response:
            if response.status != 200:
                return None

            return await response.read()
    except TimeoutError as exc:
        await logger.adebug("[HiFi] Cover download timed out", error=str(exc), url=cover_url)
        return None
    except aiohttp.ClientError as exc:
        await logger.adebug("[HiFi] Cover download failed", error=str(exc), url=cover_url)
        return None


async def download_stream_audio(
    stream: HifiTrackStream, *, max_size_bytes: int = TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
) -> tuple[bytes, str | None]:
    timeout = aiohttp.ClientTimeout(total=HIFI_DOWNLOAD_TIMEOUT_SECONDS)
    session = await HTTPClient.get_session()

    try:
        async with session.get(stream.url, timeout=timeout) as response:
            if response.status != 200:
                raise HifiRequestFailedError(response.status)

            if (content_length := response.content_length) and content_length > max_size_bytes:
                raise HifiTrackTooLargeError

            payload = await response.read()
            if len(payload) > max_size_bytes:
                raise HifiTrackTooLargeError

            content_type = response.headers.get("Content-Type")
            return payload, content_type

    except TimeoutError as exc:
        await logger.aerror("[HiFi] Download timed out", error=str(exc), url=stream.url)
        msg = "HiFi audio download timed out"
        raise HifiAPIError(msg) from exc
    except aiohttp.ClientError as exc:
        await logger.aerror("[HiFi] Download failed", error=str(exc), url=stream.url)
        msg = "HiFi audio download failed"
        raise HifiAPIError(msg) from exc
