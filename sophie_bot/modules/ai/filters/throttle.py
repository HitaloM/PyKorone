from typing import Any, Dict, Union

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Filter
from aiogram.types import Message

from sophie_bot.constants import AI_DEFAULT_DAILY_LIMIT
from sophie_bot.db.models import AIUsageModel, ChatModel
from sophie_bot.utils.i18n import gettext as _


class AIThrottleFilter(Filter):
    async def __call__(self, message: Message, chat_db: ChatModel) -> Union[bool, Dict[str, Any]]:
        usage = await AIUsageModel.get_today(chat_db.tid)

        if usage >= AI_DEFAULT_DAILY_LIMIT:
            await message.reply(_("❗️ You've reached the daily AI limit, please try again tomorrow."))
            raise SkipHandler

        await AIUsageModel.increase_today(chat_db)

        return True
