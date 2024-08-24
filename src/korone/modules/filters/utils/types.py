# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ButtonAction(Enum):
    URL = "url"


class Button(BaseModel):
    text: str
    action: ButtonAction
    data: Any
    same_row: bool = False

    def model_dump(self, **kwargs) -> dict[str, Any]:
        serialized_data = super().model_dump(**kwargs)
        serialized_data["action"] = self.action.value
        return serialized_data


class FilterFile(BaseModel):
    file_id: str = Field(alias="id")
    file_type: str = Field(alias="type")

    class Config:
        arbitrary_types_allowed = True


class Saveable(BaseModel):
    text: str = ""
    file: FilterFile | None = None
    buttons: list[list[Button]] = []


class FilterModel(BaseModel):
    filter_id: int = Field(alias="id")
    chat_id: int
    names: tuple[str, ...] = Field(default=None, alias="filter_names")
    file: FilterFile | None = None
    text: str | None = Field(default=None, alias="filter_text")
    content_type: str
    created_date: int
    creator_id: int
    edited_date: int
    editor_id: int
    buttons: list[list[Button]] = []

    class Config:
        arbitrary_types_allowed = True
