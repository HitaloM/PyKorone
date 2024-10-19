from typing import Annotated, Optional

from beanie import Document, Indexed
from beanie.odm.operators.update.general import Set
from pymongo.results import DeleteResult

from sophie_bot.db.models.notes import Saveable


class RulesModel(Saveable, Document):
    # Old ID
    chat_id: Annotated[int, Indexed()]

    class Settings:
        name = "rules"

    @staticmethod
    async def get_rules(chat_id: int) -> Optional["RulesModel"]:
        return await RulesModel.find_one(RulesModel.chat_id == chat_id)

    @staticmethod
    async def set_rules(chat_id: int, rules: Saveable) -> "RulesModel":
        data = rules.model_dump()
        data["chat_id"] = chat_id
        return await RulesModel.find_one(RulesModel.chat_id == chat_id).upsert(Set(data), on_insert=RulesModel(**data))

    @staticmethod
    async def del_rules(chat_id: int) -> Optional[DeleteResult]:
        return await RulesModel.find(RulesModel.chat_id == chat_id).delete()
