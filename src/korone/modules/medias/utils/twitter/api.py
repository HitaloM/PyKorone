# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

import httpx

from korone.utils.caching import cache
from korone.utils.logging import logger

from .types import Response, Tweet


class TwitterError(Exception):
    pass


@cache(ttl=timedelta(weeks=1))
async def fetch_tweet(url: str) -> Tweet | None:
    fx_url = re.sub(
        r"(https?://)(?:www\.)?(?:(?:twitter|x|fxtwitter|vxtwitter|fix(?:upx|vx))\.com)",
        r"\1api.fxtwitter.com",
        url,
        flags=re.IGNORECASE,
    )
    try:
        async with httpx.AsyncClient(http2=True, timeout=20) as client:
            response = await client.get(fx_url)
            response.raise_for_status()

            if response.json()["code"] != 200:
                raise TwitterError(response.json()["message"])

            model = Response.model_validate_json(response.text)
            return model.tweet
    except httpx.HTTPError as e:
        await logger.aexception("[Medias/Twitter] Error fetching tweet data: %s", e)
        raise TwitterError from e
