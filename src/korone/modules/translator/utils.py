# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass

import httpx

from korone.config import ConfigManager


class TranslationError(Exception):
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
        self.api_key = ConfigManager.get("korone", "DEEPL_KEY")
        self.url = "https://api-free.deepl.com/v2/translate"

    async def translate_text(
        self, text: str, target_lang: str, source_lang: str | None
    ) -> Translation:
        async with httpx.AsyncClient(http2=True) as client:
            try:
                data = {
                    "text": [text],
                    "auth_key": self.api_key,
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
                msg = f"HTTP error occurred: {e.response.status_code}"
                raise TranslationError(msg) from e
            except (KeyError, IndexError) as e:
                msg = "Failed to parse translation response."
                raise TranslationError(msg) from e
            except Exception as e:
                msg = f"Unexpected error: {e!s}"
                raise TranslationError(msg) from e
