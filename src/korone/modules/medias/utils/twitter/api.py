# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

import httpx

from korone import cache
from korone.modules.medias.utils.twitter.types import Response, Tweet
from korone.utils.logging import logger


class TwitterError(Exception):
    pass


@cache(ttl=timedelta(weeks=1))
async def fetch_tweet(url: str) -> Tweet | None:
    fx_url = re.sub(r"(www\.|)(twitter\.com|x\.com)", "api.fxtwitter.com", url)
    try:
        async with httpx.AsyncClient(http2=True) as client:
            response = await client.get(fx_url)
            response.raise_for_status()
            model = Response.model_validate_json(response.text)
            return model.tweet
    except httpx.HTTPError as e:
        await logger.aexception("Error fetching tweet data: %s", e)
        raise TwitterError from e
