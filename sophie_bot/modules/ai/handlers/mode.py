from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import TextArg

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(text=TextArg(l_("Prompt")))
@flags.help(description=l_("Generates a new AI mode"))
class AiGenerateMode(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("aimode"), AIEnabledFilter()

    async def handle(self) -> Any:
        user_text = self.data["text"]

        await bot.send_chat_action(self.event.chat.id, "typing")

        await ai_chatbot_reply(self.event, self.connection, user_text=user_text)
