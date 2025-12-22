from datetime import datetime, timezone

from beanie import Document
from pydantic import Field

from sophie_bot.db.models._link_type import Link
from sophie_bot.db.models.chat import ChatModel


class ApiTokenModel(Document):
    token: str = Field(..., description="Hashed token")
    label: str
    owner: Link[ChatModel]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "api_tokens"
