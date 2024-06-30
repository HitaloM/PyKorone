from typing import Annotated, Optional

from beanie import Document, Indexed, Link
from pymongo import ASCENDING, IndexModel

from sophie_bot.db.models import ChatModel


class ChatConnectionModel(Document):
    # Old IDs
    user_id: int
    chat_id: Optional[int] = None

    # New links
    group: Optional[Link[ChatModel]] = None
    user: Annotated[Optional[Link[ChatModel]], Indexed(unique=True)] = None

    class Settings:
        name = "connections"
        indexes = [
            IndexModel(
                [
                    ("user", ASCENDING),
                    ("group", ASCENDING),
                ],
                unique=True,
                name="user_group",
            ),
            IndexModel(
                [
                    ("user_id", ASCENDING),
                    ("chat_id", ASCENDING),
                ],
                unique=True,
                name="legacy_user_id_chat_id",
            ),
        ]

    @staticmethod
    async def get_by_user_id(user_id: int) -> Optional["ChatConnectionModel"]:
        return await ChatConnectionModel.find_one(ChatConnectionModel.user_id == user_id)
