from datetime import datetime
from typing import Annotated, Optional

from beanie import Document, Indexed
from pydantic import ConfigDict


class FiltersModel(Document):
    # Old ID
    chat_id: Annotated[int, Indexed(unique=True)]

    handler: str
    action: str
    time: Optional[datetime] = None

    model_config = ConfigDict(
        extra="allow",
    )

    class Settings:
        name = "filters"

    @staticmethod
    async def get_filters(chat_id: int) -> list["FiltersModel"] | None:
        return await FiltersModel.find(FiltersModel.chat_id == chat_id).to_list()
