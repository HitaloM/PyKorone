from typing import Any, Dict, Union

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Filter
from aiogram.types import Message
from stfu_tg import Doc, Italic, Template
from typing_extensions import Optional

from sophie_bot.db.models import AIEnabledModel, ChatModel
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


class AIEnabledFilter(Filter):
    @staticmethod
    async def get_status(chat_db: ChatModel) -> bool:
        return bool(await AIEnabledModel.get_state(chat_db.iid))

    async def __call__(self, message: Message, chat_db: Optional[ChatModel]) -> Union[bool, Dict[str, Any]]:
        if message.chat.type == "private":
            return True

        if not chat_db:
            log.error("AIEnabledFilter: Chat not found in database, skipping")
            raise SkipHandler

        status = await self.get_status(chat_db)

        if not status:
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
