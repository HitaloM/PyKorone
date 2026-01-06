from datetime import datetime, timezone
from typing import Annotated

from beanie import Document, Indexed
from pydantic import Field

from sophie_bot.db.db_exceptions import DBNotFoundException
from sophie_bot.db.models._link_type import Link
from sophie_bot.db.models.chat import ChatModel


class ApiTokenModel(Document):
    token_hash: Annotated[str, Indexed(unique=True)] = Field(..., description="Hashed token")
    label: str
    user: Link[ChatModel]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "api_tokens"

    @staticmethod
    async def get_by_hash(token_hash: str) -> "ApiTokenModel":
        model = await ApiTokenModel.find_one(ApiTokenModel.token_hash == token_hash, fetch_links=True)
        if not model:
            raise DBNotFoundException()
        return model
