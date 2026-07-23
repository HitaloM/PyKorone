from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.filters.chat_status import GroupChatFilter
from korone.modules.help.utils.menu import build_help_menu
from korone.utils.exception import KoroneError
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.disableable(name="help")
@flags.help(description=l_("Show the full help menu privately in this chat."))
class HelpGroupHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return Command("help"), GroupChatFilter()

    async def handle(self) -> None:
        if not self.event.from_user:
            raise KoroneError.user_context_unavailable()

        text, reply_markup = build_help_menu()
        if self.event.ephemeral_message_id is not None:
            await self.event.reply(text, reply_markup=reply_markup, disable_web_page_preview=True)
            return

        await self.event.answer(
            text,
            receiver_user_id=self.event.from_user.id,
            reply_parameters=self.event.as_reply_parameters(),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
