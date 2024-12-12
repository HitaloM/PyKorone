# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, ConfigDict, Field


class WeatherSearch(BaseModel):
    latitude: list[float]
    longitude: list[float]
    address: list[str]


class WeatherResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    weather_id: str = Field(alias="id")
    temperature: float = Field(alias="temperature")
    temperature_feels_like: float = Field(alias="temperatureFeelsLike")
    relative_humidity: float = Field(alias="relativeHumidity")
    wind_speed: float = Field(alias="windSpeed")
    wx_phrase_long: str = Field(alias="wxPhraseLong")
    city: str = Field(alias="city")
    admin_district: str = Field(alias="adminDistrict")
    country: str = Field(alias="country")
