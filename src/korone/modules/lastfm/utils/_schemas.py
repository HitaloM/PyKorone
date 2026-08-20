import html
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    OnErrorOmit,
    StringConstraints,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)
from pydantic_core import PydanticCustomError


def _non_empty_text(value: str) -> str:
    decoded = html.unescape(value).strip()
    if not decoded:
        msg = "value is empty"
        raise ValueError(msg)
    return decoded


def _integer(value: object) -> int:
    if isinstance(value, bool):
        msg = "integer_type"
        raise PydanticCustomError(msg, "Input should be a valid integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and (stripped := value.strip()).isdigit():
        return int(stripped)

    msg = "integer_type"
    raise PydanticCustomError(msg, "Input should be a valid integer")


def _none_on_error(value: object, handler: ValidatorFunctionWrapHandler) -> object:
    try:
        return handler(value)
    except ValidationError:
        return None


def _zero_on_error(value: object, handler: ValidatorFunctionWrapHandler) -> object:
    try:
        return handler(value)
    except ValidationError:
        return 0


def _singleton_or_list(value: object) -> object:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return value
    return []


def _list_or_empty(value: object) -> object:
    return value if isinstance(value, list) else []


def _now_playing(value: object) -> bool:
    return str(value).lower() == "true"


def _loved(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value == 1
    if isinstance(value, str):
        return value.strip() == "1"
    return False


type _Text = Annotated[str, StringConstraints(strict=True), AfterValidator(_non_empty_text)]
type _TransportInt = Annotated[int, BeforeValidator(_integer)]
type _OptionalField[T] = Annotated[T | None, WrapValidator(_none_on_error)]
type _OptionalText = _OptionalField[_Text]
type _OptionalInt = _OptionalField[_TransportInt]
type _DefaultInt = Annotated[_TransportInt, WrapValidator(_zero_on_error)]
type _Nodes[T] = Annotated[list[OnErrorOmit[T]], BeforeValidator(_singleton_or_list)]
type _ListNodes[T] = Annotated[list[OnErrorOmit[T]], BeforeValidator(_list_or_empty)]
type _TrackNodes = Annotated[list[object], BeforeValidator(_singleton_or_list)]


class _TransportModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class _LastFMNamedTextPayload(_TransportModel):
    text: _OptionalText = Field(default=None, alias="#text")
    name: _OptionalText = None

    @property
    def value(self) -> str | None:
        return self.text or self.name


type _LastFMName = _OptionalField[_Text | _LastFMNamedTextPayload]


class _LastFMImagePayload(_TransportModel):
    text: _OptionalText = Field(default=None, alias="#text")


class _LastFMNowPlayingPayload(_TransportModel):
    now_playing: Annotated[bool, BeforeValidator(_now_playing)] = Field(default=False, alias="nowplaying")


class _LastFMDatePayload(_TransportModel):
    uts: _OptionalInt = None


class _LastFMImageContainerPayload(_TransportModel):
    image: _ListNodes[_LastFMImagePayload] = Field(default_factory=list)


class _LastFMRecentTrackPayload(_LastFMImageContainerPayload):
    name: _OptionalText = None
    artist: _LastFMName = None
    album: _LastFMName = None
    attributes: _OptionalField[_LastFMNowPlayingPayload] = Field(default=None, alias="@attr")
    date: _OptionalField[_LastFMDatePayload] = None
    loved: Annotated[bool, BeforeValidator(_loved)] = False


class _LastFMRecentTracksPayload(_TransportModel):
    track: _Nodes[_LastFMRecentTrackPayload] = Field(default_factory=list)


class _LastFMRecentTracksResponse(_TransportModel):
    recenttracks: _OptionalField[_LastFMRecentTracksPayload] = None


class _LastFMTopAlbumPayload(_LastFMImageContainerPayload):
    name: _OptionalText = None
    artist: _LastFMName = None
    playcount: _DefaultInt = 0


class _LastFMTopAlbumsPayload(_TransportModel):
    album: _Nodes[_LastFMTopAlbumPayload] = Field(default_factory=list)


class _LastFMTopAlbumsResponse(_TransportModel):
    topalbums: _OptionalField[_LastFMTopAlbumsPayload] = None


class _LastFMTopArtistPayload(_TransportModel):
    name: _OptionalText = None
    playcount: _DefaultInt = 0


class _LastFMTopArtistsPayload(_TransportModel):
    artist: _Nodes[_LastFMTopArtistPayload] = Field(default_factory=list)


class _LastFMTopArtistsResponse(_TransportModel):
    topartists: _OptionalField[_LastFMTopArtistsPayload] = None


class _LastFMTagsPayload(_TransportModel):
    tag: _Nodes[_LastFMNamedTextPayload] = Field(default_factory=list)


class _LastFMTrackInfoPayload(_TransportModel):
    userplaycount: _DefaultInt = 0
    listeners: _DefaultInt = 0
    playcount: _DefaultInt = 0
    duration: _OptionalInt = None
    toptags: _OptionalField[_LastFMTagsPayload] = None


class _LastFMTrackInfoResponse(_TransportModel):
    track: _OptionalField[_LastFMTrackInfoPayload] = None


class _LastFMStatsPayload(_TransportModel):
    userplaycount: _DefaultInt = 0
    listeners: _DefaultInt = 0
    playcount: _DefaultInt = 0


class _LastFMArtistInfoPayload(_TransportModel):
    name: _OptionalText = None
    stats: _OptionalField[_LastFMStatsPayload] = None
    tags: _OptionalField[_LastFMTagsPayload] = None


class _LastFMArtistInfoResponse(_TransportModel):
    artist: _OptionalField[_LastFMArtistInfoPayload] = None


class _LastFMTracksPayload(_TransportModel):
    track: _TrackNodes = Field(default_factory=list)


class _LastFMAlbumInfoPayload(_LastFMImageContainerPayload):
    name: _OptionalText = None
    artist: _LastFMName = None
    userplaycount: _DefaultInt = 0
    listeners: _DefaultInt = 0
    playcount: _DefaultInt = 0
    tracks: _OptionalField[_LastFMTracksPayload] = None
    tags: _OptionalField[_LastFMTagsPayload] = None


class _LastFMAlbumInfoResponse(_TransportModel):
    album: _OptionalField[_LastFMAlbumInfoPayload] = None


class _LastFMUserPayload(_TransportModel):
    name: _OptionalText = None


class _LastFMUserResponse(_TransportModel):
    user: _OptionalField[_LastFMUserPayload] = None


class _LastFMAPIErrorPayload(_TransportModel):
    error: _OptionalInt = None
    message: _OptionalText = None


class _DeezerCoverPayload(_TransportModel):
    cover_xl: _OptionalText = None
    cover_big: _OptionalText = None
    cover_medium: _OptionalText = None
    cover_small: _OptionalText = None
    cover: _OptionalText = None


class _DeezerArtistPayload(_TransportModel):
    name: _OptionalText = None
    picture_xl: _OptionalText = None
    picture_big: _OptionalText = None
    picture_medium: _OptionalText = None
    picture_small: _OptionalText = None
    picture: _OptionalText = None


class _DeezerAlbumPayload(_DeezerCoverPayload):
    title: _OptionalText = None
    title_short: _OptionalText = None
    artist: _OptionalField[_DeezerArtistPayload] = None


class _DeezerTrackPayload(_DeezerCoverPayload):
    title: _OptionalText = None
    title_short: _OptionalText = None
    artist: _OptionalField[_DeezerArtistPayload] = None
    album: _OptionalField[_DeezerAlbumPayload] = None


class _DeezerArtistSearchPayload(_TransportModel):
    data: _ListNodes[_DeezerArtistPayload] = Field(default_factory=list)


class _DeezerAlbumSearchPayload(_TransportModel):
    data: _ListNodes[_DeezerAlbumPayload] = Field(default_factory=list)


class _DeezerTrackSearchPayload(_TransportModel):
    data: _ListNodes[_DeezerTrackPayload] = Field(default_factory=list)
