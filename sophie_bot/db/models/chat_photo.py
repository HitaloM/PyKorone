from datetime import datetime, UTC
from typing import TYPE_CHECKING

from beanie import Document, Link
from bson import ObjectId
from pydantic import Field

if TYPE_CHECKING:
    from sophie_bot.db.models import ChatModel


class ChatPhotoModel(Document):
    chat: Link["ChatModel"]
    url: str
    last_updated: datetime = Field(default_factory=lambda _: datetime.now(tz=UTC))

    class Settings:
        name = "chat_photo"

    @staticmethod
    async def upsert_photo(chat_iid: ObjectId, url: str):
        photo = await ChatPhotoModel.find_one(ChatPhotoModel.chat.iid == chat_iid)
        if photo:
            photo.url = url
            photo.last_updated = datetime.now(tz=UTC)
            await photo.save()
        else:
            await ChatPhotoModel(chat=chat_iid, url=url).insert()
