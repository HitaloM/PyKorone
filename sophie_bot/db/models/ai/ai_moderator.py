from __future__ import annotations
from enum import Enum
from beanie import Document, PydanticObjectId

from sophie_bot.db.models._link_type import Link
from sophie_bot.db.models.chat import ChatModel


class DetectionLevel(str, Enum):
    OFF = "off"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class AIModeratorModel(Document):
    chat: Link[ChatModel]
    enabled: bool = True

    sexual: DetectionLevel = DetectionLevel.NORMAL
    hate_and_discrimination: DetectionLevel = DetectionLevel.NORMAL
    violence_and_threats: DetectionLevel = DetectionLevel.NORMAL
    dangerous_and_criminal_content: DetectionLevel = DetectionLevel.NORMAL
    selfharm: DetectionLevel = DetectionLevel.NORMAL
    health: DetectionLevel = DetectionLevel.NORMAL
    financial: DetectionLevel = DetectionLevel.NORMAL
    law: DetectionLevel = DetectionLevel.NORMAL
    pii: DetectionLevel = DetectionLevel.NORMAL

    class Settings:
        name = "ai_moderator"

    @staticmethod
    async def get_state(chat_iid: PydanticObjectId) -> bool:
        usage = await AIModeratorModel.find_one(AIModeratorModel.chat.id == chat_iid)
        return usage.enabled if usage else False

    @staticmethod
    async def set_state(chat: "ChatModel", new_state: bool):
        model = await AIModeratorModel.find_one(AIModeratorModel.chat.id == chat.iid)
        if model:
            model.enabled = new_state
            return await model.save()

        if not new_state:
            return None

        model = AIModeratorModel(chat=chat, enabled=True)
        return await model.save()
