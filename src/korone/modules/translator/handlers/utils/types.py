# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel


class Translation(BaseModel):
    detected_source_language: str
    text: str


class TranslationResponse(BaseModel):
    translations: list[Translation]
