from typing import Any, Dict, Union

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Filter
from aiogram.types import Message
from stfu_tg import Doc, Italic, Template

from sophie_bot.db.models import AIEnabledModel, ChatModel
from sophie_bot.utils.i18n import gettext as _


class AIEnabledFilter(Filter):
    @staticmethod
    async def get_status(chat_db: ChatModel) -> bool:
        return bool(await AIEnabledModel.get_state(chat_db.id))

    async def __call__(self, message: Message, chat_db: ChatModel) -> Union[bool, Dict[str, Any]]:
        if not self.get_status(chat_db):
            await message.reply(
                str(
                    Doc(
                        _("The AI Features are currently deactivated for this chat."),
                        Template(_('Please use "{cmd}" to activate them.'), cmd=Italic("/enableai yes")),
                    )
                )
            )
            raise SkipHandler

        return True
