from datetime import datetime, timezone
from typing import Any

from beanie import Document
from pydantic import Field

from sophie_bot.db.models._link_type import Link
from sophie_bot.db.models.chat import ChatModel


class LogModel(Document):
    chat: Link[ChatModel]
    user: Link[ChatModel]
    event: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "logs"
