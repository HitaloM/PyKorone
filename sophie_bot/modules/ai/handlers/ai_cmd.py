from typing import Optional

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import OptionalArg, TextArg

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(
    text=OptionalArg(TextArg(l_("Prompt"))),
)
@flags.help(description=l_("Ask Sophie a question"))
@flags.ai_cache(cache_handler_result=True)
@flags.disableable(name="ai")
class AiCmd(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("ai"), AIEnabledFilter()

    async def handle(self):
        user_text: Optional[str] = self.data["text"]

        return await ai_chatbot_reply(self.event, self.connection, user_text)
