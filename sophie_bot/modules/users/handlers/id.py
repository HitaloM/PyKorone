from typing import Any, Optional

from aiogram import flags
from aiogram.handlers import MessageHandler

from ass_tg.types import UserArg, OptionalArg
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from stfu_tg import Doc, Code, Template


@flags.args(
    user=OptionalArg(UserArg(l_('User')))
)
class ShowIDs(MessageHandler):
    async def handle(self) -> Any:
        chat: ChatConnection = self.data["connection"]
        user: Optional[Any] = self.data['user']

        doc = Doc()

        if self.event.from_user:
            user_id = self.event.from_user.id
            doc += Template(_("Your ID: {id}"), id=Code(user_id))

        if self.event.chat.type != "private":
            doc += Template(_("Chat ID: {id}"), id=Code(self.event.chat.id))

        if chat.is_connected:
            doc += Template(_("Connected chat ID: {id}"), id=Code(chat.id))

        # Replied user ID

        if self.event.reply_to_message and self.event.reply_to_message.from_user:
            user_id = self.event.reply_to_message.from_user.id
            doc += Template(_("Replied user ID: {id}"), id=Code(user_id))

        if user:
            doc += user

        return await self.event.reply(str(doc))
