# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class LastFMImage(BaseModel):
    size: str
    url: str = Field(alias="#text")


class LastFMArtist(BaseModel):
    name: str
    playcount: int = 0
    loved: int | None = None
    images: list[LastFMImage] | None = Field(default=None, alias="image")
    tags: list[str] | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Any) -> list[str] | None:
        return [tag["name"] for tag in v.get("tag", [])] if v else None


class LastFMAlbum(BaseModel):
    artist: LastFMArtist | None = None
    name: str
    playcount: int = 0
    loved: int | None = None
    images: list[LastFMImage] | None = Field(default=None, alias="image")
    tags: list[str] | str = ""

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, values: dict[str, Any]) -> dict[str, Any]:
        aliases = {
            "name": ["title", "#text"],
            "playcount": ["userplaycount", "playcount"],
        }

        for field, possible_aliases in aliases.items():
            for alias in possible_aliases:
                if alias in values:
                    values[field] = values.pop(alias)
                    break

        return values

    @field_validator("artist", mode="before")
    @classmethod
    def validate_artist(cls, v: Any) -> LastFMArtist | Any:
        return LastFMArtist(name=v) if isinstance(v, str) else v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Any) -> list[str] | str:
        return [tag["name"] for tag in v["tag"]] if isinstance(v, dict) else v


class LastFMTrack(BaseModel):
    artist: LastFMArtist
    name: str
    album: LastFMAlbum | None = None
    loved: int = 0
    images: list[LastFMImage] | None = Field(default=None, alias="image")
    now_playing: bool = Field(default=False, alias="@attr")
    playcount: int = 0
    played_at: int | None = Field(default=None, alias="date")
    tags: list[str] | None = Field(default=None, alias="toptags")

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, values: dict[str, Any]) -> dict[str, Any]:
        aliases = {"playcount": ["userplaycount", "playcount"]}

        for field, possible_aliases in aliases.items():
            for alias in possible_aliases:
                if alias in values:
                    values[field] = values.pop(alias)
                    break

        return values

    @field_validator("played_at", mode="before")
    @classmethod
    def validate_played_at(cls, v: Any) -> int | None:
        return v.get("uts", None) if v else None

    @field_validator("now_playing", mode="before")
    @classmethod
    def validate_now_playing(cls, v: Any) -> bool:
        return v.get("nowplaying", False) if v else False

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Any) -> list[str] | None:
        return [tag["name"] for tag in v.get("tag", [])] if v else None


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
    def validate_registered(cls, v: Any) -> int:
        return int(v["unixtime"]) if isinstance(v, dict) else int(v)


class DeezerImage(BaseModel):
    url: str


class DeezerArtist(BaseModel):
    id: int
    name: str
    image: DeezerImage
