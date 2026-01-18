from beanie import Document, PydanticObjectId

from sophie_bot.db.models._link_type import Link
from sophie_bot.db.models.chat import ChatModel


class AIEnabledModel(Document):
    chat: Link[ChatModel]

    class Settings:
        name = "ai_enabled"

    @staticmethod
    async def get_state(chat_iid: PydanticObjectId) -> bool:
        usage = await AIEnabledModel.find_one(AIEnabledModel.chat.id == chat_iid)

        if not usage:
            return False

        return True

    @staticmethod
    async def set_state(chat: "ChatModel", new_state: bool):
        model = await AIEnabledModel.find_one(AIEnabledModel.chat.id == chat.iid)
        if model and not new_state:
            return await model.delete()

        elif model:
            return model

        model = AIEnabledModel(chat=chat)
        return await model.save()
