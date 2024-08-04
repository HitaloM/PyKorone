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


class TwitterAPI:
    __slots__ = ("url",)

    def __init__(self, url: str):
        self.url = url

    @staticmethod
    def _convert_to_fx_url(url: str) -> str:
        return re.sub(r"(www\.|)(twitter\.com|x\.com)", "api.fxtwitter.com", url)

    @cache(ttl=timedelta(weeks=1), key="tweet_data:{self.url}")
    async def fetch(self) -> Tweet | None:
        fx_url = self._convert_to_fx_url(self.url)
        try:
            async with httpx.AsyncClient(http2=True) as client:
                response = await client.get(fx_url)
                response.raise_for_status()
                return Response.model_validate_json(response.text).tweet
        except httpx.HTTPError as e:
            await logger.aexception("Error fetching tweet data: %s", e)
            raise TwitterError from e
