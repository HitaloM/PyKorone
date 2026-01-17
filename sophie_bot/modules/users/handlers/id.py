from typing import Any, Optional

from aiogram import Router
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import OptionalArg
from stfu_tg import Code, Doc, Template, UserLink

from sophie_bot.args.users import SophieUserArg
from sophie_bot.db.models import ChatModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_

router = Router(name="users")


async def optional_user(message: Message | None, _data: dict):
    if message and message.reply_to_message:
        return {}

    return {"user": OptionalArg(SophieUserArg(l_("User")))}


@router.message(CMDFilter("id"), flags={"args": optional_user})
class ShowIDHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("id")),

    async def handle(self) -> Any:
        chat: ChatConnection = self.data["connection"]
        user: Optional[ChatModel] = self.data.get("user", None)

        doc = Doc()

        if self.event.from_user:
            user_id = self.event.from_user.id
            doc += Template(_("Your ID: {id}"), id=Code(user_id))

        if self.event.chat.type != "private":
            doc += Template(_("Chat ID: {id}"), id=Code(self.event.chat.id))

        if chat.is_connected:
            doc += Template(_("Connected chat ID: {id}"), id=Code(chat.tid))

        # Replied user ID

        if self.event.reply_to_message and self.event.reply_to_message.from_user:
            user_id = self.event.reply_to_message.from_user.id
            doc += Template(_("Replied user ID: {id}"), id=Code(user_id))

        if user:
            doc += Template(
                _("{user}'s ID: {id}"),
                user=UserLink(user_id=user.tid, name=user.first_name_or_title),
                id=Code(user.tid),
            )

        return await self.event.reply(str(doc))
