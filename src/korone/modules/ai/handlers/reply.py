from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags

from korone.config import CONFIG
from korone.filters.chat_status import GroupChatFilter
from korone.modules.ai.filters import AIEnabledFilter, AIThrottleFilter
from korone.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from korone.modules.ai.utils.self_reply import is_ai_message
from korone.utils.handlers import KoroneMessageHandler

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message


def _is_ai_reply_message(message: Message) -> bool:
    if not message.reply_to_message:
        return False

    if message.text and message.text.startswith(tuple(CONFIG.commands_prefix)):
        return False

    reply = message.reply_to_message
    if reply.from_user and reply.from_user.id != CONFIG.bot_id:
        return False

    return is_ai_message(reply.text or reply.caption or "")


@flags.help(exclude=True)
class AiReplyHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (_is_ai_reply_message, GroupChatFilter(), AIThrottleFilter(), AIEnabledFilter())

    async def handle(self) -> Message:
        return await ai_chatbot_reply(self.event, self.chat)
