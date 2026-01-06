from beanie import Document, PydanticObjectId

from ._link_type import Link
from .chat import ChatModel


class AIMemoryModel(Document):
    chat: Link[ChatModel]
    lines: list[str] = []

    class Settings:
        name = "ai_memory"

    @staticmethod
    async def get_lines(chat_iid: PydanticObjectId) -> list[str]:
        model = await AIMemoryModel.find_one(AIMemoryModel.chat.id == chat_iid)

        return model.lines if model else []

    @staticmethod
    async def append_line(chat: "ChatModel", new_line: str):
        model = await AIMemoryModel.find_one(AIMemoryModel.chat.id == chat.iid)
        if not model:
            model = AIMemoryModel(chat=chat)

        model.lines = [*model.lines, new_line] if model else [new_line]
        await model.save()

    @staticmethod
    async def clear(chat_iid: PydanticObjectId):
        model = await AIMemoryModel.find_one(AIMemoryModel.chat.id == chat_iid)
        if model:
            await model.delete()
