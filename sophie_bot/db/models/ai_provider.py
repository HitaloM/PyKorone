from __future__ import annotations

from beanie import Document, PydanticObjectId
from pydantic import Field

from ._link_type import Link
from .chat import ChatModel


class AIProviderModel(Document):
    chat: Link[ChatModel]
    provider: str = Field(default="auto")  # stores AIProviders enum name ('auto' | 'openai' | 'google')

    class Settings:
        name = "ai_provider"

    @staticmethod
    async def get_provider_name(chat_iid: PydanticObjectId) -> str | None:
        model = await AIProviderModel.find_one(AIProviderModel.chat.id == chat_iid)
        return model.provider if model else None

    @staticmethod
    async def set_provider(chat: ChatModel, provider_name: str) -> AIProviderModel:
        model = await AIProviderModel.find_one(AIProviderModel.chat.id == chat.iid)
        if model:
            model.provider = provider_name
            await model.save()
            return model
        model = AIProviderModel(chat=chat, provider=provider_name)
        return await model.save()

    async def reset_to_auto(self):
        await self.delete()
