# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

import httpx

from korone.modules.medias.utils.common import ensure_url_scheme
from korone.modules.medias.utils.generic_headers import GENERIC_HEADER
from korone.utils.caching import cache
from korone.utils.logging import get_logger

from .types import Response, Tweet

logger = get_logger(__name__)


class TwitterError(Exception):
    pass


@cache(ttl=timedelta(weeks=1))
async def fetch_tweet(url: str) -> Tweet | None:
    normalized_url = ensure_url_scheme(url)
    fx_url = re.sub(
        r"(https?://)(?:www\.)?(?:(?:twitter|x|fxtwitter|vxtwitter|fix(?:upx|vx))\.com)",
        r"\1api.fxtwitter.com",
        normalized_url,
        flags=re.IGNORECASE,
    )
    try:
        async with httpx.AsyncClient(http2=True, timeout=20, headers=GENERIC_HEADER) as client:
            response = await client.get(fx_url)
            response.raise_for_status()

            try:
                response_data = response.json()
            except Exception as e:
                await logger.aexception("[Medias/Twitter] JSON parse failed: %s", e)
                msg = "Invalid JSON response"
                raise TwitterError(msg) from e

            if not isinstance(response_data, dict):
                msg = "Invalid response format"
                raise TwitterError(msg)

            if response_data.get("code") != 200:
                error_message = response_data.get("message", "Unknown error")
                raise TwitterError(str(error_message))

            try:
                model = Response.model_validate_json(response.text)
                return model.tweet
            except Exception as e:
                await logger.aexception("[Medias/Twitter] Model validation failed: %s", e)
                msg = "Invalid response model"
                raise TwitterError(msg) from e
    except httpx.HTTPError as e:
        await logger.aexception("[Medias/Twitter] Fetch failed: %s", e)
        raise TwitterError from e
