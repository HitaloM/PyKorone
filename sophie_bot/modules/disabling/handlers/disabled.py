from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Section

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.disabling.utils.get_disabled import get_disabled_handlers
from sophie_bot.modules.help.utils.format_help import format_handlers
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Lists all disabled commands."))
@flags.disableable(name="disabled")
class ListDisabled(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("disabled"),)

    async def handle(self):
        connection: ChatConnection = self.data["connection"]

        disabled = await get_disabled_handlers(connection.tid)

        if not disabled:
            await self.event.reply(_("No disabled commands found."))
            return

        await self.event.reply(str(Section(format_handlers(disabled), title=_("Disabled commands"))))
