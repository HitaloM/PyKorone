from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command
from stfu_tg import Doc, Section

from korone.filters.user_status import IsOP
from korone.modules.help.utils.extract_info import HELP_MODULES
from korone.modules.help.utils.format_help import format_handlers
from korone.utils.handlers import KoroneMessageHandler

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description="Shows a list of all OP-only commands")
class OpCMDSList(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return Command("op_cmds"), IsOP(is_op=True)

    async def handle(self) -> None:
        await self.event.reply(
            str(
                Doc(
                    *(
                        Section(
                            format_handlers([h for h in module.handlers if h.only_op]),
                            title=f"{module.name} {module.icon}",
                        )
                        for module in HELP_MODULES.values()
                        if any(h.only_op for h in module.handlers)
                    )
                )
            )
        )
