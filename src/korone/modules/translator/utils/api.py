# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import random

import httpx
from anyio import sleep

from korone.config import ConfigManager
from korone.utils.logging import get_logger

from .errors import QuotaExceededError, TranslationError
from .types import Translation, TranslationResponse

logger = get_logger(__name__)

API_KEY: str = ConfigManager.get("korone", "DEEPL_KEY")


class DeepL:
    def __init__(self) -> None:
        self.url = "https://api-free.deepl.com/v2/translate"
        self.max_retries = 5

    async def translate_text(
        self, text: str, target_lang: str, source_lang: str | None
    ) -> Translation:
        async with httpx.AsyncClient(http2=True) as client:
            retries = 0

            while retries < self.max_retries:
                try:
                    data = self._prepare_request_data(text, target_lang, source_lang)
                    response = await client.post(self.url, data=data)
                    response.raise_for_status()
                    return self._parse_response(response)

                except httpx.HTTPStatusError as e:
                    if not await self._handle_http_error(e, retries):
                        break
                    retries += 1

                except (KeyError, IndexError) as e:
                    msg = "[DeepL] Failed to parse translation response."
                    raise TranslationError(msg) from e

                except Exception as e:
                    msg = f"[DeepL] Unexpected error: {e!s}"
                    raise TranslationError(msg) from e

            msg = "[DeepL] Maximum retries exceeded."
            raise TranslationError(msg)

    @staticmethod
    def _prepare_request_data(text: str, target_lang: str, source_lang: str | None) -> dict:
        data = {
            "text": [text],
            "auth_key": API_KEY,
            "target_lang": target_lang.upper(),
        }
        if source_lang:
            data["source_lang"] = source_lang.upper()
        return data

    @staticmethod
    def _parse_response(response: httpx.Response) -> Translation:
        response_data = response.json()
        logger.debug("[DeepL] Response data: %s", response_data)
        translation_response = TranslationResponse(**response_data)

        if not translation_response.translations:
            msg = "[DeepL] No translations found in the response."
            raise TranslationError(msg)

        return translation_response.translations[0]

    @staticmethod
    async def _handle_http_error(e: httpx.HTTPStatusError, retries: int) -> bool:
        status_code = e.response.status_code
        backoff = 2**retries + random.uniform(0, 1)
        if status_code == 429:
            await logger.aerror("[DeepL] Rate limit exceeded, retrying in %s seconds...", backoff)
            await sleep(backoff)
            return True
        if status_code == 456:
            msg = "[DeepL] Quota exceeded."
            await logger.aerror(msg)
            raise QuotaExceededError(msg) from e
        if status_code == 500:
            await logger.adebug(
                "[DeepL] Internal server error, retrying in %s seconds...", backoff
            )
            await sleep(backoff)
            return True
        msg = f"[DeepL] HTTP error occurred: {status_code}"
        raise TranslationError(msg) from e
