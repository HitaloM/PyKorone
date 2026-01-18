from datetime import date

from beanie import Document

from sophie_bot.db.models._link_type import Link
from sophie_bot.db.models.chat import ChatModel


class AIUsageModel(Document):
    chat: Link[ChatModel]
    days: dict[date, int]

    class Settings:
        name = "ai_usage"

    @staticmethod
    async def get_today(chat_id: int) -> int:
        usage = await AIUsageModel.find_one(AIUsageModel.chat.id == chat_id)

        if not usage:
            return 0

        return usage.days.get(date.today(), 0)

    @staticmethod
    async def increase_today(chat: "ChatModel") -> "AIUsageModel":
        usage = await AIUsageModel.find_one(AIUsageModel.chat.id == chat.iid)

        date_today = date.today()
        if not usage:
            usage = AIUsageModel(chat=chat, days={date_today: 1})

        usage.days[date_today] = usage.days.get(date_today, 0) + 1
        return await usage.save()
