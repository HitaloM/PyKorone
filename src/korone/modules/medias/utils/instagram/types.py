# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, Field, HttpUrl


class InstaFixData(BaseModel):
    title: str | None = None
    media_type: str | None = Field(default=None, alias="type")
    media_url: HttpUrl | None = None
    username: str | None = None
    description: str | None = None
