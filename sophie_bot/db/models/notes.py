from datetime import datetime
from enum import Enum
from typing import Annotated, Optional, Sequence

from aiogram.enums import ContentType
from beanie import Document, Indexed, Link
from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.find.evaluation import Text
from pydantic import BaseModel, Field
from pymongo import TEXT
from pymongo.results import DeleteResult

from .chat import ChatModel
from .notes_buttons import Button


class NoteFile(BaseModel):
    id: str
    type: ContentType

    class Config:
        arbitrary_types_allowed = True


class SaveableParseMode(Enum):
    markdown = "md"
    html = "html"


CURRENT_SAVEABLE_VERSION = 2


class Saveable(BaseModel):
    text: Annotated[Optional[str], Indexed(index_type=TEXT)] = ""

    file: Optional[NoteFile] = None
    buttons: list[list[Button]] = Field(default_factory=list)

    parse_mode: Optional[SaveableParseMode] = SaveableParseMode.html
    preview: Optional[bool] = False

    version: Optional[int] = 1


class NoteModel(Saveable, Document):
    # Old ID
    chat_tid: Annotated[int, Indexed()] = Field(..., alias="chat_id")

    # New link
    chat: Annotated[Optional[Link[ChatModel]], Indexed()] = None

    names: tuple[str, ...]
    note_group: Optional[str] = None

    description: Optional[str] = None
    ai_description: bool = False

    created_date: Optional[datetime] = None
    created_user: Optional[int] = None
    edited_date: Optional[datetime] = None
    edited_user: Optional[int] = None

    class Settings:
        name = "notes"

    @staticmethod
    async def get_chat_notes(chat_tid: int) -> list["NoteModel"]:
        return await NoteModel.find(NoteModel.chat_tid == chat_tid).to_list()

    @staticmethod
    async def search_chat_notes(chat_tid: int, text: str) -> list["NoteModel"]:
        return await NoteModel.find(NoteModel.chat_tid == chat_tid, Text(text)).to_list()

    @staticmethod
    async def get_by_notenames(chat_tid: int, notenames: Sequence[str]) -> Optional["NoteModel"]:
        return await NoteModel.find_one(NoteModel.chat_tid == chat_tid, In(NoteModel.names, notenames))

    @staticmethod
    async def delete_all_notes(chat_tid: int) -> DeleteResult | None:
        return await NoteModel.find(NoteModel.chat_tid == chat_tid).delete()
