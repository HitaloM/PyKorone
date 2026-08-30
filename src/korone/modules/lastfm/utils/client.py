import aiohttp
import orjson
from pydantic import BaseModel, TypeAdapter, ValidationError

from korone.config import CONFIG
from korone.http import HttpClient, http_client

from ._schemas import (
    _LastFMAlbumInfoResponse,
    _LastFMAPIErrorPayload,
    _LastFMArtistInfoResponse,
    _LastFMImagePayload,
    _LastFMName,
    _LastFMNamedTextPayload,
    _LastFMRecentTracksResponse,
    _LastFMTagsPayload,
    _LastFMTopAlbumsResponse,
    _LastFMTopArtistsResponse,
    _LastFMTrackInfoResponse,
    _LastFMUserResponse,
)
from .errors import LastFMAPIError, LastFMConfigurationError, LastFMPayloadError, LastFMRequestError
from .types import (
    LastFMAlbumInfo,
    LastFMArtistInfo,
    LastFMRecentTrack,
    LastFMTopAlbum,
    LastFMTopArtist,
    LastFMTrackInfo,
)

LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"
LASTFM_TIMEOUT_SECONDS = 20
LASTFM_PLACEHOLDER_IMAGE = "2a96cbd8b46e442fc41c2b86b821562f"
_ROOT_PAYLOAD_ADAPTER = TypeAdapter(dict[str, object])


def _validate_payload[T: BaseModel](model_type: type[T], payload: object) -> T:
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        msg = "Last.fm returned an unexpected payload format."
        raise LastFMPayloadError(msg) from exc


def _name(value: _LastFMName) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, _LastFMNamedTextPayload):
        return value.value
    return None


def _best_image(images: list[_LastFMImagePayload]) -> str | None:
    for image in reversed(images):
        if not image.text or LASTFM_PLACEHOLDER_IMAGE in image.text:
            continue
        return image.text

    return None


def _tags(payload: _LastFMTagsPayload | None) -> tuple[str, ...]:
    if payload is None:
        return ()

    parsed: list[str] = []
    seen: set[str] = set()
    for item in payload.tag:
        tag_name = item.value
        if not tag_name:
            continue

        normalized = tag_name.lower()
        if normalized in seen:
            continue

        seen.add(normalized)
        parsed.append(tag_name)

    return tuple(parsed)


class LastFMClient:
    __slots__ = ("api_key", "base_url", "http", "timeout")

    def __init__(
        self, api_key: str | None = None, base_url: str = LASTFM_BASE_URL, *, http: HttpClient = http_client
    ) -> None:
        configured_key = CONFIG.lastfm_key.get_secret_value() if CONFIG.lastfm_key is not None else ""
        resolved_key = (api_key or configured_key).strip()
        if not resolved_key:
            msg = "Last.fm API key is not configured."
            raise LastFMConfigurationError(msg)

        self.api_key = resolved_key
        self.base_url = base_url
        self.http = http
        self.timeout = aiohttp.ClientTimeout(total=LASTFM_TIMEOUT_SECONDS)

    async def _request(self, *, method: str, params: dict[str, str | int]) -> dict[str, object]:
        request_params: dict[str, str | int] = {"method": method, "api_key": self.api_key, "format": "json", **params}

        session = self.http.session
        try:
            async with session.get(self.base_url, params=request_params, timeout=self.timeout) as response:
                raw_payload: object
                try:
                    raw_payload = await response.json(content_type=None, loads=orjson.loads)
                except (aiohttp.ContentTypeError, ValueError) as exc:
                    msg = "Last.fm returned an invalid JSON payload."
                    raise LastFMPayloadError(msg) from exc

                try:
                    payload = _ROOT_PAYLOAD_ADAPTER.validate_python(raw_payload)
                except ValidationError as exc:
                    msg = "Last.fm returned an unexpected payload format."
                    raise LastFMPayloadError(msg) from exc

                error_payload = _validate_payload(_LastFMAPIErrorPayload, payload)
                if payload.get("error") is not None:
                    raise LastFMAPIError(
                        error_payload.message or "Last.fm API error.", error_code=error_payload.error or None
                    )

                if response.status != 200:
                    msg = f"Last.fm request failed with status {response.status}."
                    raise LastFMRequestError(msg, status_code=response.status)

                return payload
        except TimeoutError as exc:
            msg = "Last.fm request timed out."
            raise LastFMRequestError(msg) from exc
        except aiohttp.ClientError as exc:
            msg = "Last.fm request failed."
            raise LastFMRequestError(msg) from exc

    async def get_recent_tracks(self, *, username: str, limit: int = 3) -> list[LastFMRecentTrack]:
        payload = await self._request(
            method="user.getrecenttracks", params={"user": username, "extended": 1, "limit": max(1, limit)}
        )
        response = _validate_payload(_LastFMRecentTracksResponse, payload)
        if response.recenttracks is None:
            return []

        parsed_tracks: list[LastFMRecentTrack] = []
        for track_payload in response.recenttracks.track:
            name = track_payload.name
            artist = _name(track_payload.artist)
            if not name or not artist:
                continue

            parsed_tracks.append(
                LastFMRecentTrack(
                    name=name,
                    artist=artist,
                    album=_name(track_payload.album),
                    image_url=_best_image(track_payload.image),
                    now_playing=bool(track_payload.attributes and track_payload.attributes.now_playing),
                    played_at=track_payload.date.uts if track_payload.date else None,
                    loved=track_payload.loved,
                )
            )

        return parsed_tracks

    async def get_top_albums(self, *, username: str, period: str = "overall", limit: int = 9) -> list[LastFMTopAlbum]:
        payload = await self._request(
            method="user.gettopalbums", params={"user": username, "period": period, "limit": max(1, limit)}
        )

        response = _validate_payload(_LastFMTopAlbumsResponse, payload)
        if response.topalbums is None:
            return []

        albums: list[LastFMTopAlbum] = []
        for album_payload in response.topalbums.album:
            album_name = album_payload.name
            album_artist = _name(album_payload.artist)
            if not album_name or not album_artist:
                continue

            albums.append(
                LastFMTopAlbum(
                    name=album_name,
                    artist=album_artist,
                    playcount=album_payload.playcount,
                    image_url=_best_image(album_payload.image),
                )
            )

        return albums

    async def get_top_artists(
        self, *, username: str, period: str = "overall", limit: int = 100
    ) -> list[LastFMTopArtist]:
        payload = await self._request(
            method="user.gettopartists", params={"user": username, "period": period, "limit": max(1, limit)}
        )

        response = _validate_payload(_LastFMTopArtistsResponse, payload)
        if response.topartists is None:
            return []

        artists: list[LastFMTopArtist] = []
        for artist_payload in response.topartists.artist:
            artist_name = artist_payload.name
            if not artist_name:
                continue

            artists.append(LastFMTopArtist(name=artist_name, playcount=artist_payload.playcount))

        return artists

    async def get_track_info(self, *, username: str, artist: str, track: str) -> LastFMTrackInfo | None:
        payload = await self._request(
            method="track.getInfo", params={"artist": artist, "track": track, "username": username}
        )

        response = _validate_payload(_LastFMTrackInfoResponse, payload)
        if response.track is None or not response.track.model_fields_set:
            return None

        track_payload = response.track
        return LastFMTrackInfo(
            user_playcount=track_payload.userplaycount,
            listeners=track_payload.listeners,
            playcount=track_payload.playcount,
            duration_ms=track_payload.duration or None,
            tags=_tags(track_payload.toptags),
        )

    async def get_artist_info(self, *, username: str, artist: str) -> LastFMArtistInfo | None:
        payload = await self._request(method="artist.getInfo", params={"artist": artist, "username": username})

        response = _validate_payload(_LastFMArtistInfoResponse, payload)
        if response.artist is None or not response.artist.model_fields_set:
            return None

        artist_payload = response.artist
        stats = artist_payload.stats
        return LastFMArtistInfo(
            name=artist_payload.name or artist,
            user_playcount=stats.userplaycount if stats else 0,
            listeners=stats.listeners if stats else 0,
            playcount=stats.playcount if stats else 0,
            tags=_tags(artist_payload.tags),
        )

    async def get_album_info(self, *, username: str, artist: str, album: str) -> LastFMAlbumInfo | None:
        payload = await self._request(
            method="album.getInfo", params={"artist": artist, "album": album, "username": username}
        )

        response = _validate_payload(_LastFMAlbumInfoResponse, payload)
        if response.album is None or not response.album.model_fields_set:
            return None

        album_payload = response.album
        return LastFMAlbumInfo(
            name=album_payload.name or album,
            artist=_name(album_payload.artist) or artist,
            user_playcount=album_payload.userplaycount,
            listeners=album_payload.listeners,
            playcount=album_payload.playcount,
            track_count=len(album_payload.tracks.track) if album_payload.tracks else 0,
            tags=_tags(album_payload.tags),
            image_url=_best_image(album_payload.image),
        )

    async def user_exists(self, *, username: str) -> bool:
        try:
            payload = await self._request(method="user.getInfo", params={"user": username})
        except LastFMAPIError as exc:
            if exc.error_code == 6:
                return False
            raise

        response = _validate_payload(_LastFMUserResponse, payload)
        return response.user is not None and response.user.name is not None
