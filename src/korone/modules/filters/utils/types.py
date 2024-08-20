# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, Field


class FilterModel(BaseModel):
    filter_id: int = Field(alias="id")
    chat_id: int
    filter_name: str = Field(alias="filter")
    file_id: str | None = None
    message: str | None = None
    content_type: str
    created_date: int
    created_user: int
    edited_date: int
    edited_user: int
