# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from contextlib import asynccontextmanager
from datetime import timedelta

import httpx
import orjson
from cashews import NOT_NONE

from korone.utils.caching import cache
from korone.utils.logging import logger

from .types import RunRequest, RunResponse

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
    text = text.strip()
    try:
        lang, code = text.split(" ", 1)
    except ValueError as err:
        msg = "Input must contain both language and code."
        raise ValueError(msg) from err

    code = code.lstrip()
    stdin = None

    if stdin_match := STDIN_PATTERN.search(code):
        start, end = stdin_match.span()
        stdin = code[end + 1 :].strip()
        code = code[:start].strip()

    if not code:
        msg = "Bad query: Code is empty."
        raise ValueError(msg)

    return RunRequest(language=lang, code=code, stdin=stdin)


@cache(ttl=timedelta(weeks=1), condition=NOT_NONE)
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
