from __future__ import annotations

from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import BufferedInputFile, Message
from ass_tg.types import TextArg, WordArg, OptionalArg, OneOf
from ass_tg.types.base_abc import ArgFabric

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.services.bot import bot
from sophie_bot.utils.emoji_banner import EmojiBanner


class OpBannerHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("op_banner"), IsOP(True)

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        # emojis is a single token; text is freeform; color is optional and validated via ASS OneOf
        return {
            "emojis": WordArg("Emoji(s)"),
            "color": OptionalArg(OneOf(("pink", "red", "blue", "green"))),
            "text": TextArg("Text", parse_entities=True),
        }

    async def handle(self) -> Any:
        emojis: str = self.data["emojis"]
        text: str = self.data["text"]
        color: str | None = self.data.get("color")

        img = EmojiBanner.render(emojis, text, color=color)
        await bot.send_photo(chat_id=self.event.chat.id, photo=BufferedInputFile(img, "banner.jpeg"))
