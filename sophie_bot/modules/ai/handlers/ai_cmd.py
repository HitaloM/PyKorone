from typing import Optional

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import OptionalArg, TextArg

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from sophie_bot.modules.connections.utils.connection import set_connected_chat
from sophie_bot.middlewares.connections import ConnectionsMiddleware
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import lazy_gettext as l_, gettext as _


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

        if self.event.chat.type == "private" and self.connection.is_connected:
            await set_connected_chat(self.event.from_user.id, None)
            await self.event.reply(_("You have been automatically disconnected from the chat to use AI."))
            # Refresh connection to local context
            self.data["connection"] = await ConnectionsMiddleware.get_current_chat_info(self.event.chat)

        return await ai_chatbot_reply(self.event, self.connection, user_text)
