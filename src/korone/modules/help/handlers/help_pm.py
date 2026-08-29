from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.filters.chat_status import PrivateChatFilter
from korone.modules.help.args import HELP_ARGUMENTS, HelpArguments
from korone.modules.help.utils.menu import build_rich_help_menu
from korone.modules.help.utils.presentation import build_module_search
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(
    description=l_("Show the full help menu or search for a module."), examples=((l_("Open module help"), "disabling"),)
)
class HelpPMHandler(KoroneMessageHandler[HelpArguments]):
    arguments = HELP_ARGUMENTS

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return Command("help"), PrivateChatFilter()

    async def handle(self) -> None:
        if self.args.query is None:
            rich_message, reply_markup = build_rich_help_menu()
        else:
            rich_message, reply_markup = build_module_search(self.args.query)

        await self.event.answer_rich(rich_message, reply_markup=reply_markup)
