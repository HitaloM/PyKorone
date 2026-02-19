from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.enums import ChatType
from aiogram.filters import Filter
from stfu_tg import Doc, Italic, Template

from korone.logger import get_logger
from korone.modules.ai.utils.settings import is_ai_enabled
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import Message

    from korone.db.models.chat import ChatModel

logger = get_logger(__name__)


class AIEnabledFilter(Filter):
    @staticmethod
    async def get_status(chat_db: ChatModel) -> bool:
        return await is_ai_enabled(chat_db.chat_id)

    async def __call__(self, message: Message, chat_db: ChatModel | None = None) -> bool:
        if message.chat.type == ChatType.PRIVATE:
            return True

        if chat_db is None:
            logger.error("AIEnabledFilter: Chat not found in database, skipping")
            raise SkipHandler

        if await self.get_status(chat_db):
            return True

        await message.reply(
            str(
                Doc(
                    _("The AI features are currently disabled for this chat."),
                    Template(_('Please use "{cmd}" to activate them.'), cmd=Italic("/enableai yes")),
                )
            )
        )
        raise SkipHandler
