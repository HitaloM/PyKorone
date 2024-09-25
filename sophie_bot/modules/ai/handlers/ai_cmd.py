from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import MessageHandler
from ass_tg.types import TextArg

from sophie_bot import bot
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.utils.ai_chatbot import handle_message
from sophie_bot.modules.ai.utils.message_history import get_message_history
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(text=TextArg(l_("Prompt")))
@flags.help(description=l_("Ask Sophie a question"))
class AiCmd(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("ai"), AIEnabledFilter()

    async def handle(self):
        user_text = self.data["text"]

        await bot.send_chat_action(self.event.chat.id, "typing")
        await handle_message(self.event, user_text, await get_message_history(self.event, self.data))
