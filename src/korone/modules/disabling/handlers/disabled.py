from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command
from stfu_tg import Section

from korone.modules.disabling.utils.get_disabled import get_disabled_handlers
from korone.modules.help.utils.format_help import format_handlers
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("List commands currently disabled in this chat."))
@flags.disableable(name="disabled")
class ListDisabled(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("disabled"),)

    async def handle(self) -> None:
        disabled = await get_disabled_handlers(self.chat.chat_id)

        if not disabled:
            await self.event.reply(_("No disabled commands found."))
            return

        await self.event.reply(
            str(
                Section(
                    format_handlers(
                        disabled,
                        show_only_in_groups=False,
                        show_disable_able=False,
                        show_description=False,
                        show_args=False,
                    ),
                    title=_("Disabled commands"),
                )
            )
        )
