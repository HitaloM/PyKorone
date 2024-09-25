from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import MessageHandler
from aiogram.types import Message

from sophie_bot import CONFIG, bot
from sophie_bot.modules.ai.filters.throttle import AIThrottleFilter
from sophie_bot.modules.ai.utils.ai_chatbot import handle_message
from sophie_bot.modules.ai.utils.message_history import get_message_history
from sophie_bot.modules.ai.utils.self_reply import is_ai_message


class AiReplyHandler(MessageHandler):
    @staticmethod
    async def filter(message: Message):
        if not message.reply_to_message:
            return False

        if message.reply_to_message.from_user and message.reply_to_message.from_user.id != CONFIG.bot_id:
            return False

        if is_ai_message(message.reply_to_message.text or ""):
            return True

        return False

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return AiReplyHandler.filter, AIThrottleFilter()

    async def handle(self) -> Any:
        text = self.event.text or ""

        await bot.send_chat_action(self.event.chat.id, "typing")
        await handle_message(self.event, text, await get_message_history(self.event, self.data))
