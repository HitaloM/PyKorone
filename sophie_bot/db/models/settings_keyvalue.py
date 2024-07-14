from typing import Any, Optional

from beanie import Document, UpdateResponse
from beanie.odm.operators.update.general import Set


class GlobalSettings(Document):
    key: str
    value: Any

    class Settings:
        name = "global_settings"

    @staticmethod
    async def get_by_key(key: str) -> Optional["GlobalSettings"]:
        return await GlobalSettings.find_one(GlobalSettings.key == key)

    @staticmethod
    async def set_by_key(key: str, value: Any) -> "GlobalSettings":
        return await GlobalSettings.find_one(GlobalSettings.key == key).upsert(
            Set({GlobalSettings.value: value}),
            on_insert=GlobalSettings(
                key=key,
                value=value,
            ),
            response_type=UpdateResponse.NEW_DOCUMENT,
        )
