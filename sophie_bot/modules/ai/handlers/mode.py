from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import MessageHandler
from ass_tg.types import TextArg

from sophie_bot.db.models import ChatModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(text=TextArg(l_("Prompt")))
@flags.help(description=l_("Generates a new AI mode"))
class AiGenerateMode(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("aimode"), AIEnabledFilter()

    async def handle(self):
        user_text = self.data["text"]

        await bot.send_chat_action(self.event.chat.id, "typing")

        # Get chat from database and create connection
        chat_db = await ChatModel.get_by_tid(self.event.chat.id)
        if not chat_db:
            return

        connection = ChatConnection(
            type=chat_db.type,
            is_connected=False,
            id=chat_db.chat_id,
            title=chat_db.first_name_or_title,
            db_model=chat_db,
        )
        await ai_chatbot_reply(self.event, connection, user_text=user_text)
