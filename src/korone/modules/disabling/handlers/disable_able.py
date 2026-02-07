from typing import TYPE_CHECKING

from aiogram import flags
from stfu_tg import Section

from korone.filters.cmd import CMDFilter
from korone.modules.help.utils.extract_info import DISABLEABLE_CMDS
from korone.modules.help.utils.format_help import format_handlers
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.modules.help.utils.extract_info import HandlerHelp


@flags.help(description=l_("Lists all commands that can be disabled."))
@flags.disableable(name="disableable")
class ListDisableable(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("disableable"),)

    @staticmethod
    def get_disable_able_commands() -> list[HandlerHelp]:
        return [x for x in DISABLEABLE_CMDS if x.disableable]

    async def handle(self) -> None:
        await self.event.reply(
            str(
                Section(
                    format_handlers(
                        self.get_disable_able_commands(),
                        show_only_in_groups=False,
                        show_disable_able=False,
                        show_description=False,
                        show_args=False,
                    ),
                    title=_("Disable-able commands"),
                )
            )
        )
