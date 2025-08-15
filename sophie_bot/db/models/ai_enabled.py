from beanie import Document, Link

from .chat import ChatModel


class AIEnabledModel(Document):
    chat: Link[ChatModel]

    class Settings:
        name = "ai_enabled"

    @staticmethod
    async def get_state(chat_tid: int) -> bool:
        from .chat import ChatModel

        chat = await ChatModel.get_by_chat_id(chat_tid)
        if not chat:
            return False

        usage = await AIEnabledModel.find_one(AIEnabledModel.chat.id == chat.id)

        if not usage:
            return False

        return True

    @staticmethod
    async def set_state(chat: "ChatModel", new_state: bool):
        model = await AIEnabledModel.find_one(AIEnabledModel.chat.id == chat.id)
        if model and not new_state:
            return await model.delete()

        elif model:
            return model

        model = AIEnabledModel(chat=chat)
        return await model.save()
