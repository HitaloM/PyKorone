from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Section

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.help.utils.extract_info import DISABLEABLE_CMDS, HandlerHelp
from sophie_bot.modules.help.utils.format_help import format_handlers
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Lists all commands that can be disabled."))
@flags.disableable(name="disableable")
class ListDisableable(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("disableable"),)

    @staticmethod
    def get_disable_able_commands() -> list[HandlerHelp]:
        return list(x for x in DISABLEABLE_CMDS if x.disableable)

    async def handle(self) -> Any:
        await self.event.reply(
            str(
                Section(
                    format_handlers(
                        self.get_disable_able_commands(), show_only_in_groups=False, show_disable_able=False
                    ),
                    title=_("Disable-able commands"),
                )
            )
        )
