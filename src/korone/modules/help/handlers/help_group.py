from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import EphemeralMessageParameters

from korone.filters.chat_status import GroupChatFilter
from korone.modules.help.args import HELP_ARGUMENTS, HelpArguments
from korone.modules.help.utils.menu import build_rich_help_menu
from korone.modules.help.utils.presentation import build_module_search
from korone.utils.exception import KoroneError
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import lazy_gettext as l_
from korone.utils.telegram_errors import is_bot_not_admin_error

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.disableable(name="help")
@flags.help(
    description=l_("Show the full help menu privately or search for a module in this chat."),
    examples=((l_("Open module help"), "disabling"),),
)
class HelpGroupHandler(KoroneMessageHandler[HelpArguments]):
    arguments = HELP_ARGUMENTS

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return Command("help"), GroupChatFilter()

    async def handle(self) -> None:
        if not self.event.from_user:
            raise KoroneError.user_context_unavailable()

        if self.args.query is None:
            rich_message, reply_markup = build_rich_help_menu()
        else:
            rich_message, reply_markup = build_module_search(self.args.query)
        if self.event.ephemeral_message_id is not None:
            try:
                await self.event.answer_rich(
                    rich_message,
                    ephemeral_message_parameters=EphemeralMessageParameters(receiver_user_id=self.event.from_user.id),
                    reply_markup=reply_markup,
                )
            except TelegramBadRequest as error:
                if not is_bot_not_admin_error(error):
                    raise
                await self.event.answer_rich(rich_message, reply_markup=reply_markup)
            return

        try:
            await self.event.answer_rich(
                rich_message,
                ephemeral_message_parameters=EphemeralMessageParameters(receiver_user_id=self.event.from_user.id),
                reply_parameters=self.event.as_reply_parameters(),
                reply_markup=reply_markup,
            )
        except TelegramBadRequest as error:
            if not is_bot_not_admin_error(error):
                raise
            await self.event.reply_rich(rich_message, reply_markup=reply_markup)
