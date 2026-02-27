from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.filters.user_status import IsOP
from korone.utils.handlers import KoroneMessageHandler

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=("Crash the bot intentionally for operator testing."))
class CrashHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("op_crash"), IsOP(is_op=True))

    async def handle(self) -> None:
        await self.event.reply("Crashing...")

        _ = 1 / 0
