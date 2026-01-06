from datetime import datetime, timezone
from typing import Annotated

from beanie import Document, Indexed
from pydantic import Field

from sophie_bot.db.db_exceptions import DBNotFoundException
from sophie_bot.db.models._link_type import Link
from sophie_bot.db.models.chat import ChatModel


class RefreshTokenModel(Document):
    token_hash: Annotated[str, Indexed(unique=True)]
    user: Link[ChatModel]
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "refresh_tokens"

    @staticmethod
    async def get_by_hash(token_hash: str) -> "RefreshTokenModel":
        model = await RefreshTokenModel.find_one(RefreshTokenModel.token_hash == token_hash, fetch_links=True)
        if not model:
            raise DBNotFoundException()
        return model
