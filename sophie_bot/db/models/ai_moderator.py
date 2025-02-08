from beanie import Document, Link

from .chat import ChatModel


class AIModeratorModel(Document):
    chat: Link[ChatModel]

    class Settings:
        name = "ai_enabled"

    @staticmethod
    async def get_state(chat_id: int) -> bool:
        usage = await AIModeratorModel.find_one(AIModeratorModel.chat.id == chat_id)

        if not usage:
            return False

        return True

    @staticmethod
    async def set_state(chat: "ChatModel", new_state: bool):
        model = await AIModeratorModel.find_one(AIModeratorModel.chat.id == chat.id)
        if model and not new_state:
            return await model.delete()

        elif model:
            return model

        model = AIModeratorModel(chat=chat)
        return await model.save()
