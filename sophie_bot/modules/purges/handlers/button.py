from typing import Any

from aiogram import F
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message as AiogramMessage

from sophie_bot.modules.utils_.base_handler import SophieCallbackQueryHandler
from sophie_bot.modules.utils_.common_try import common_try


class LegacyDelMsgButton(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (F.data.regexp(r"btn_deletemsg_cb_"),)

    async def handle(self) -> Any:
        message = self.event.message
        if not isinstance(message, AiogramMessage):
            return

        await common_try(message.delete())
