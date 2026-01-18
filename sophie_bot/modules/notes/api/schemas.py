from __future__ import annotations

from datetime import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel

from sophie_bot.db.models.notes import NoteFile, SaveableParseMode
from sophie_bot.db.models.notes_buttons import Button
from sophie_bot.utils.api.schemas import RestSaveable


class NoteResponse(RestSaveable):
    id: PydanticObjectId
    names: tuple[str, ...]
    file: NoteFile | None
    parse_mode: SaveableParseMode | None
    description: str | None
    ai_description: bool
    note_group: str | None
    created_date: datetime | None
    edited_date: datetime | None


class NoteCreate(RestSaveable):
    names: tuple[str, ...]
    file: NoteFile | None = None
    parse_mode: SaveableParseMode = SaveableParseMode.html
    description: str | None = None
    ai_description: bool = False
    note_group: str | None = None


class NoteUpdate(BaseModel):
    names: tuple[str, ...] | None = None
    text: str | None = None
    file: NoteFile | None = None
    buttons: list[list[Button]] | None = None
    parse_mode: SaveableParseMode | None = None
    preview: bool | None = None
    description: str | None = None
    ai_description: bool | None = None
    note_group: str | None = None
