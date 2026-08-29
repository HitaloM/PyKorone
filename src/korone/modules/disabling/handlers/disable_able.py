from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.modules.help.utils.extract_info import DISABLEABLE_CMDS
from korone.modules.help.utils.format_help import format_handlers
from korone.ui import section
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.modules.help.utils.extract_info import HandlerHelp


@flags.help(description=l_("List commands that can be disabled in this chat."))
@flags.disableable(name="disableable")
class ListDisableable(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("disableable"),)

    @staticmethod
    def get_disable_able_commands() -> list[HandlerHelp]:
        return list(DISABLEABLE_CMDS)

    async def handle(self) -> None:
        await self.answer(
            section(
                _("Toggleable commands"),
                format_handlers(
                    self.get_disable_able_commands(),
                    show_only_in_groups=False,
                    show_disable_able=False,
                    show_description=False,
                    show_args=False,
                ),
            )
        )
