from typing import Optional

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import MessageHandler
from ass_tg.types import OptionalArg, TextArg

from sophie_bot import CONFIG, bot
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.utils.ai_chatbot import DEFAULT_MODEL, Models, ai_reply
from sophie_bot.modules.ai.utils.message_history import AIMessageHistory
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(
    text=OptionalArg(TextArg(l_("Prompt"))),
)
@flags.help(description=l_("Ask Sophie a question"))
@flags.ai_cache(cache_handler_result=True)
@flags.disableable(name="ai")
class AiCmd(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("ai"), AIEnabledFilter()

    async def handle(self):
        user_text: Optional[str] = self.data["text"]

        await bot.send_chat_action(self.event.chat.id, "typing")

        model = DEFAULT_MODEL
        if self.from_user and self.from_user.id == CONFIG.owner_id and user_text and user_text.endswith("?"):
            model = Models.GPT_4O

        messages = await AIMessageHistory.chatbot(
            self.event, custom_user_text=user_text, add_from_message=bool(user_text)
        )

        return await ai_reply(self.event, messages, model=model)
