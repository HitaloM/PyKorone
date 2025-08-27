from __future__ import annotations

from typing import Any, Dict

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import BufferedInputFile
from ass_tg.types import TextArg, WordArg, OptionalArg, OneOf

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.services.bot import bot
from sophie_bot.utils.emoji_banner import EmojiBanner


class OpBannerHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("op_banner"), IsOP(True)

    @classmethod
    async def handler_args(cls, message, data: Dict) -> Dict[str, object]:
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
