# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from dataclasses import dataclass

import httpx

from korone.config import ConfigManager
from korone.utils.logging import logger

API_KEY: str = ConfigManager.get("korone", "DEEPL_KEY")


class TranslationError(Exception):
    pass


class QuotaExceededError(TranslationError):
    pass


@dataclass(frozen=True, slots=True)
class Translation:
    detected_source_language: str
    text: str


@dataclass(frozen=True, slots=True)
class TranslationResponse:
    translations: list[Translation]

    @staticmethod
    def from_dict(data: dict) -> "TranslationResponse":
        translations = [Translation(**translation) for translation in data["translations"]]
        return TranslationResponse(translations=translations)


class DeepL:
    def __init__(self) -> None:
        self.url = "https://api-free.deepl.com/v2/translate"
        self.max_retries = 5

    async def translate_text(
        self, text: str, target_lang: str, source_lang: str | None
    ) -> Translation:
        async with httpx.AsyncClient(http2=True) as client:
            retries = 0
            backoff = 1

            while retries < self.max_retries:
                try:
                    data = {
                        "text": [text],
                        "auth_key": API_KEY,
                        "target_lang": target_lang.upper(),
                    }
                    if source_lang is not None:
                        data["source_lang"] = source_lang.upper()

                    response = await client.post(self.url, data=data)
                    response.raise_for_status()
                    response_data = response.json()
                    translation_response = TranslationResponse.from_dict(response_data)
                    return translation_response.translations[0]

                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code
                    if status_code == 429:
                        logger.debug(
                            "[DeepL] Rate limit exceeded, retrying in %s seconds...", backoff
                        )
                        await asyncio.sleep(backoff)
                        retries += 1
                        backoff *= 2
                    elif status_code == 456:
                        msg = "Quota exceeded."
                        logger.error(msg)
                        raise QuotaExceededError(msg) from e
                    elif status_code == 500:
                        logger.debug(
                            "[DeepL] Internal server error, retrying in %s seconds...", backoff
                        )
                        await asyncio.sleep(backoff)
                        retries += 1
                        backoff *= 2
                    else:
                        msg = f"HTTP error occurred: {status_code}"
                        logger.error(msg)
                        raise TranslationError(msg) from e

                except (KeyError, IndexError) as e:
                    msg = "Failed to parse translation response."
                    logger.error(msg)
                    raise TranslationError(msg) from e

                except Exception as e:
                    msg = f"Unexpected error: {e!s}"
                    logger.error(msg)
                    raise TranslationError(msg) from e

            msg = "Maximum retries exceeded."
            logger.error(msg)
            raise TranslationError(msg)
