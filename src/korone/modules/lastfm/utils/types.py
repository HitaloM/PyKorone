from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator


class LastFMImage(BaseModel):
    size: str
    url: str = Field(alias="#text")


class LastFMArtist(BaseModel):
    name: str
    playcount: int = 0
    images: list[LastFMImage] | None = Field(default=None, alias="image")
    tags: list[str] | str = ""

    _alias_map: ClassVar[dict[str, list[str]]] = {"playcount": ["userplaycount", "playcount", "stats"]}

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, values: dict[str, Any]) -> dict[str, Any]:
        for field, possible_aliases in cls._alias_map.items():
            for alias in possible_aliases:
                if alias in values:
                    values[field] = values.pop(alias)
                    break
        return values

    @field_validator("playcount", mode="before")
    @classmethod
    def validate_playcount(cls, v: dict[str, str | int] | str | int) -> int:
        if isinstance(v, dict):
            return int(v.get("userplaycount", v.get("playcount", 0)))
        if isinstance(v, (str, int)):
            return int(v)
        return 0

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: dict[str, list[dict[str, str]] | dict[str, str]] | list[str] | str) -> list[str] | str:
        if isinstance(v, dict):
            tags = v.get("tag", [])
            if isinstance(tags, dict):
                return [tags.get("name", "")]
            return [tag["name"] for tag in tags]
        return v


class LastFMAlbum(BaseModel):
    artist: LastFMArtist | None = None
    name: str
    playcount: int = 0
    images: list[LastFMImage] | None = Field(default=None, alias="image")
    tags: list[str] | str = ""

    _alias_map: ClassVar[dict[str, list[str]]] = {
        "name": ["title", "#text"],
        "playcount": ["userplaycount", "playcount"],
    }

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, values: dict[str, Any]) -> dict[str, Any]:
        for field, possible_aliases in cls._alias_map.items():
            for alias in possible_aliases:
                if alias in values:
                    values[field] = values.pop(alias)
                    break
        return values

    @field_validator("artist", mode="before")
    @classmethod
    def validate_artist(cls, v: str | LastFMArtist) -> LastFMArtist:
        return LastFMArtist(name=v) if isinstance(v, str) else v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: dict[str, list[dict[str, str]] | dict[str, str]] | list[str] | str) -> list[str] | str:
        if isinstance(v, dict):
            tags = v.get("tag", [])
            if isinstance(tags, dict):
                return [tags.get("name", "")]
            return [tag["name"] for tag in tags]
        return v


class LastFMTrack(BaseModel):
    artist: LastFMArtist
    name: str
    album: LastFMAlbum | None = None
    loved: int = 0
    images: list[LastFMImage] | None = Field(default=None, alias="image")
    now_playing: bool = Field(default=False, alias="@attr")
    playcount: int = 0
    played_at: int | None = Field(default=None, alias="date")
    tags: list[str] | str = Field(default="", alias="toptags")

    _alias_map: ClassVar[dict[str, list[str]]] = {"playcount": ["userplaycount", "playcount"]}

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, values: dict[str, Any]) -> dict[str, Any]:
        for field, possible_aliases in cls._alias_map.items():
            for alias in possible_aliases:
                if alias in values:
                    values[field] = values.pop(alias)
                    break
        return values

    @field_validator("played_at", mode="before")
    @classmethod
    def validate_played_at(cls, v: dict[str, str] | None) -> int | None:
        uts = v.get("uts") if v and isinstance(v, dict) else None
        return int(uts) if uts is not None else None

    @field_validator("now_playing", mode="before")
    @classmethod
    def validate_now_playing(cls, v: dict[str, str] | None) -> bool:
        return bool(v.get("nowplaying")) if v and isinstance(v, dict) else False

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: dict[str, list[dict[str, str]] | dict[str, str]] | list[str] | str) -> list[str] | str:
        if isinstance(v, dict):
            tags = v.get("tag", [])
            if isinstance(tags, dict):
                return [tags.get("name", "")]
            return [tag["name"] for tag in tags]
        return v


class LastFMUser(BaseModel):
    username: str = Field(alias="name")
    realname: str
    playcount: int
    artist_count: int
    track_count: int
    album_count: int
    registered: int
    images: list[LastFMImage] | None = Field(default=None, alias="image")

    @field_validator("registered", mode="before")
    @classmethod
    def validate_registered(cls, v: dict[str, str] | str | int) -> int:
        if isinstance(v, dict) and "unixtime" in v:
            return int(v["unixtime"])
        if isinstance(v, (str, int, float)):
            return int(v)
        msg = "Invalid type for registered field"
        raise ValueError(msg)


class DeezerData(BaseModel):
    deezer_id: int = Field(alias="id")
    deezer_type: str = Field(alias="type")
    name: str
    link: str
    nb_album: int
    nb_fan: int
    radio: bool
    tracklist: str
    picture: str | None = None
    picture_small: str | None = None
    picture_medium: str | None = None
    picture_big: str | None = None
    picture_xl: str | None = None
