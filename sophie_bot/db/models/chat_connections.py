from typing import Annotated, Optional

from beanie import Document, Indexed, Link
from pymongo import ASCENDING, IndexModel

from sophie_bot.db.models import ChatModel


class ChatConnectionModel(Document):
    # Old IDs
    user_id: int
    chat_id: int

    # New links
    group: Optional[Link[ChatModel]]
    user: Annotated[Optional[Link[ChatModel]], Indexed(unique=True)]

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
