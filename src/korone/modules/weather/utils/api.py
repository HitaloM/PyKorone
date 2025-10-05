# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from datetime import timedelta
from typing import Any

import httpx

from korone.utils.caching import cache
from korone.utils.logging import get_logger

logger = get_logger(__name__)

WEATHER_API_KEY = "8de2d8b3a93542c9a2d8b3a935a2c909"
LOCATION_SEARCH_URL = "https://api.weather.com/v3/location/search"
WEATHER_OBSERVATIONS_URL = (
    "https://api.weather.com/v3/aggcommon/v3-wx-observations-current;v3-location-point"
)
FORMAT = "json"
UNITS = "m"


async def fetch_json(url: str, params: dict) -> dict:
    async with httpx.AsyncClient(http2=True, timeout=httpx.Timeout(10.0)) as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as err:
            await logger.aexception("[Weather] HTTP error occurred: %s", err)
            return {}


@cache(ttl=timedelta(days=1))
async def search_location(query: str, language: str) -> dict[str, Any]:
    params = {
        "apiKey": WEATHER_API_KEY,
        "query": query,
        "language": language,
        "format": FORMAT,
    }
    return await fetch_json(LOCATION_SEARCH_URL, params)


async def get_weather_observations(
    latitude: float, longitude: float, language: str
) -> dict[str, Any]:
    params = {
        "apiKey": WEATHER_API_KEY,
        "geocode": f"{latitude},{longitude}",
        "language": language,
        "units": UNITS,
        "format": FORMAT,
    }
    return await fetch_json(WEATHER_OBSERVATIONS_URL, params)
