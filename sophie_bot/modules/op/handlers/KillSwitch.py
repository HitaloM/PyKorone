from __future__ import annotations

from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import BooleanArg, OptionalArg, WordArg
from ass_tg.types.base_abc import ArgFabric

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.feature_flags import (
    is_enabled,
    list_all,
    set_enabled,
    FEATURE_FLAGS,
)


class KillSwitchHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("op_killswitch"), IsOP(True)

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        # feature and value are both optional to allow listing when none provided
        return {
            "feature": OptionalArg(WordArg("feature")),
            "value": OptionalArg(BooleanArg("value")),
        }

    async def handle(self) -> Any:
        feature: str | None = self.data.get("feature")
        value: bool | None = self.data.get("value")

        if not feature and value is None:
            # List all
            states = await list_all()
            lines = [f"{k}: {str(v).lower()}" for k, v in states.items()]
            return await self.event.reply("\n".join(lines))

        if not feature or value is None:
            allowed = ", ".join(FEATURE_FLAGS)
            return await self.event.reply(f"Usage: /op_killswitch <feature> <true|false>\nAllowed features: {allowed}")

        if feature not in FEATURE_FLAGS:
            allowed = ", ".join(FEATURE_FLAGS)
            return await self.event.reply(f"Unknown feature '{feature}'. Allowed: {allowed}")

        await set_enabled(feature, value)
        # Read back for confirmation (uses in-memory cache)
        current = await is_enabled(feature)
        return await self.event.reply(f"{feature}: {str(current).lower()}")
