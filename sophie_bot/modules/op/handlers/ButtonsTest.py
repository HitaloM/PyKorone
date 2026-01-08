from __future__ import annotations

from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types.base_abc import ArgFabric

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.parse_arg import ButtonsArgList
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler


class ButtonsTestHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("op_buttons"), IsOP(True)

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {
            "buttons": ButtonsArgList(),
        }

    async def handle(self) -> Any:
        buttons = self.data.get("buttons")
        return await self.event.reply(f"Buttons: {buttons}")
