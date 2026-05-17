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


@flags.help(description="List operator-only commands.")
class OpCMDSList(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return Command("op_cmds"), IsOP(is_op=True)

    async def handle(self) -> None:
        sections = []

        for module in HELP_MODULES.values():
            ops = [handler for handler in module.handlers if handler.only_op]
            if not ops:
                continue

            sections.append(Section(format_handlers(ops), title=f"{module.name} {module.icon}"))

        await self.event.reply(str(Doc(*sections)))
