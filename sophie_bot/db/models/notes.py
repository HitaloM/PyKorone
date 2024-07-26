from datetime import datetime
from enum import Enum
from typing import Annotated, Any, List, Optional

from aiogram.enums import ContentType
from beanie import Document, Indexed, Link
from beanie.odm.operators.find.comparison import In
from pydantic import BaseModel

from sophie_bot.db.models import ChatModel


class NoteFile(BaseModel):
    id: str
    type: ContentType

    class Config:
        arbitrary_types_allowed = True


class SaveableParseMode(Enum):
    markdown = "md"
    html = "html"


class ButtonAction(Enum):
    url = "url"
    delmsg = "delmsg"


class Button(BaseModel):
    text: str
    action: ButtonAction
    data: Any


class Saveable(BaseModel):
    text: Optional[str] = ""
    file: Optional[NoteFile] = None
    buttons: list[list[Button]] = []

    parse_mode: Optional[SaveableParseMode] = SaveableParseMode.html
    preview: Optional[bool] = False


class NoteModel(Saveable, Document):
    # Old ID
    chat_id: Annotated[int, Indexed()]

    # New link
    chat: Annotated[Optional[Link[ChatModel]], Indexed()] = None

    names: tuple[str, ...]
    note_group: Optional[str] = None
    description: Optional[str] = None

    created_date: Optional[datetime] = None
    created_user: Optional[int] = None
    edited_date: Optional[datetime] = None
    edited_user: Optional[int] = None

    class Settings:
        name = "notes"

    @staticmethod
    async def get_chat_notes(chat_id: int) -> List["NoteModel"]:
        return await NoteModel.find(NoteModel.chat_id == chat_id).to_list()

    @staticmethod
    async def get_by_notenames(chat_id: int, notenames: tuple[str, ...]) -> Optional["NoteModel"]:
        return await NoteModel.find_one(NoteModel.chat_id == chat_id, In(NoteModel.names, notenames))
