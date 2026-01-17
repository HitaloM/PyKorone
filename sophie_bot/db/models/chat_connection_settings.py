from typing import Optional

from beanie import Document
from pymongo import ASCENDING, IndexModel


class ChatConnectionSettingsModel(Document):
    chat_id: int
    allow_users_connect: bool = True

    class Settings:
        name = "chat_connection_settings"
        indexes = [
            IndexModel(
                [("chat_id", ASCENDING)],
                unique=True,
                name="chat_id_index",
            ),
        ]

    @staticmethod
    async def get_by_chat_id(chat_id: int) -> Optional["ChatConnectionSettingsModel"]:
        return await ChatConnectionSettingsModel.find_one(ChatConnectionSettingsModel.chat_id == chat_id)
