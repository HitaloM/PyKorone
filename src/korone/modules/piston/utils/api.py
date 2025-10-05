# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import re
from contextlib import asynccontextmanager
from datetime import timedelta

import httpx
import orjson
from cashews import NOT_NONE

from korone.utils.caching import cache
from korone.utils.logging import get_logger

from .types import RunRequest, RunResponse

logger = get_logger(__name__)

STDIN_PATTERN = re.compile(r"\s/stdin\b")


@asynccontextmanager
async def get_async_client():
    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        yield client


@cache(ttl=timedelta(weeks=1), condition=NOT_NONE)
async def get_languages() -> list[str] | None:
    url = "https://emkc.org/api/v2/piston/runtimes"
    async with get_async_client() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            languages_map = response.json()
            language_set = {entry["language"] for entry in languages_map}
            return sorted(language_set)
        except (httpx.HTTPStatusError, Exception) as err:
            await logger.aerror("[Piston] Error fetching languages: %s", err)
            return None


def create_request(text: str) -> RunRequest:
    lang, code = "", ""
    for index, char in enumerate(text):
        if char in {" ", "\n"}:
            lang, code = text[:index], text[index + 1 :]
            break

    if not code:
        msg = "Bad query: Code is empty."
        raise ValueError(msg)

    code = code.lstrip(" \n")

    stdin = None
    stdin_match = STDIN_PATTERN.search(code)
    if stdin_match:
        start, end = stdin_match.span()
        if end + 1 < len(code):
            code, stdin = code[:start], code[end + 1 :]

    return RunRequest(language=lang, code=code, stdin=stdin)


async def run_code(request: RunRequest) -> RunResponse:
    url = "https://emkc.org/api/v2/piston/execute"
    json_body = orjson.dumps(request.to_dict())
    async with get_async_client() as client:
        try:
            response = await client.post(
                url, content=json_body, headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            return RunResponse.from_api_response(data)
        except (httpx.HTTPStatusError, Exception) as err:
            await logger.aerror("[Piston] Error running code: %s", err)
            return RunResponse(result="error", output=str(err))
