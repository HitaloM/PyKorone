from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from sophie_bot.db.models.notes import NoteFile, SaveableParseMode, Button


class NoteResponse(BaseModel):
    names: tuple[str, ...]
    text: str | None
    file: NoteFile | None
    buttons: list[list[Button]]
    parse_mode: SaveableParseMode | None
    preview: bool | None
    description: str | None
    ai_description: bool
    note_group: str | None
    created_date: datetime | None
    edited_date: datetime | None


class NoteCreate(BaseModel):
    names: tuple[str, ...]
    text: str | None = ""
    file: NoteFile | None = None
    buttons: list[list[Button]] = []
    parse_mode: SaveableParseMode = SaveableParseMode.html
    preview: bool = False
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
