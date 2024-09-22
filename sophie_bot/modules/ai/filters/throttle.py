from typing import Any, Dict, Union

from aiogram.filters import Filter
from aiogram.types import Message

from sophie_bot.db.models import AIUsageModel, ChatModel
from sophie_bot.utils.i18n import gettext as _

DAY_LIMIT = 70


class AIThrottleFilter(Filter):
    async def __call__(self, message: Message, chat_db: ChatModel) -> Union[bool, Dict[str, Any]]:
        usage = await AIUsageModel.get_today(chat_db.id)

        if usage >= DAY_LIMIT:
            await message.reply(_("❗️ You've reached the daily AI limit, please try again tomorrow."))
            return False

        await AIUsageModel.increase_today(chat_db)

        return True
