from beanie import Document, PydanticObjectId

from sophie_bot.db.models._link_type import Link
from sophie_bot.db.models.chat import ChatModel


class AIAutotranslateModel(Document):
    chat: Link[ChatModel]

    class Settings:
        name = "ai_autotranslate"

    @staticmethod
    async def get_state(chat_id: PydanticObjectId) -> bool:
        state = await AIAutotranslateModel.find_one(AIAutotranslateModel.chat.id == chat_id)

        if not state:
            return False

        return True

    @staticmethod
    async def set_state(chat: "ChatModel", new_state: bool):
        model = await AIAutotranslateModel.find_one(AIAutotranslateModel.chat.id == chat.iid)
        if model and not new_state:
            return await model.delete()

        elif model:
            return model

        model = AIAutotranslateModel(chat=chat)
        return await model.save()
