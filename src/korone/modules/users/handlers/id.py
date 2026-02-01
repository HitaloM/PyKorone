from typing import TYPE_CHECKING

from aiogram import Router, flags
from ass_tg.types import OptionalArg
from stfu_tg import Code, Doc, Template, UserLink

from korone.args.users import KoroneUserArg
from korone.filters.cmd import CMDFilter
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.db.models.chat import ChatModel

router = Router(name="users")


@flags.help(description=l_("Show user and chat IDs"))
@flags.disableable(name="id")
@router.message(CMDFilter("id"))
@flags.args(user=OptionalArg(KoroneUserArg(l_("User"))))
class ShowIDHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("id"),)

    async def handle(self) -> None:
        user: ChatModel | None = self.data.get("user", None)

        doc = Doc()

        if self.event.from_user:
            user_id = self.event.from_user.id
            doc += Template(_("Your ID: {id}"), id=Code(user_id))

        if self.event.chat.type != "private":
            doc += Template(_("Chat ID: {id}"), id=Code(self.event.chat.id))

        if self.event.reply_to_message and self.event.reply_to_message.from_user:
            user_id = self.event.reply_to_message.from_user.id
            doc += Template(_("Replied user ID: {id}"), id=Code(user_id))

        if user:
            doc += Template(
                _("{user}'s ID: {id}"), user=UserLink(user_id=user.id, name=user.first_name_or_title), id=Code(user.id)
            )

        await self.event.reply(str(doc))
        return
