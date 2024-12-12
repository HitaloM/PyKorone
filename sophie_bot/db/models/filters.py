from typing import Annotated, Any, Optional

from beanie import Document, Indexed
from pydantic import ConfigDict, Field


class FiltersModel(Document):
    # Old ID
    chat_id: Annotated[int, Indexed(unique=False)]

    handler: str

    action: Optional[str]  # None for modern filters
    actions: list[str] = Field(default_factory=list)

    time: Optional[Any] = None

    model_config = ConfigDict(
        extra="allow",
    )

    class Settings:
        name = "filters"

    @staticmethod
    async def get_filters(chat_id: int) -> list["FiltersModel"] | None:
        return await FiltersModel.find(FiltersModel.chat_id == chat_id).to_list()
