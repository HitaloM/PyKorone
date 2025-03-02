# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ButtonAction(StrEnum):
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


class UserModel(BaseModel):
    user_id: int = Field(alias="id")
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language: str = "en"
    registry_date: int | None = None


class FilterModel(BaseModel):
    filter_id: int = Field(alias="id")
    chat_id: int
    names: tuple[str, ...] = Field(default=None, alias="filter_names")
    file: FilterFile | None = None
    text: str | None = Field(default=None, alias="filter_text")
    content_type: str
    created_date: int
    creator: UserModel = Field(alias="creator_id")
    edited_date: int
    editor: UserModel = Field(alias="editor_id")
    buttons: list[list[Button]] = []

    @model_validator(mode="before")
    @classmethod
    def convert_ids_to_user_model(cls, values):
        creator_id = values.get("creator_id")
        editor_id = values.get("editor_id")

        if isinstance(creator_id, int):
            values["creator_id"] = UserModel(id=creator_id)
        if isinstance(editor_id, int):
            values["editor_id"] = UserModel(id=editor_id)

        return values

    class Config:
        arbitrary_types_allowed = True
