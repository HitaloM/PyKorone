from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import BufferedInputFile

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.modules.welcomesecurity.utils_.emoji_captcha import EmojiCaptcha
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Generate a test emoji captcha"))
class OpCaptchaHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("op_captcha"), IsOP(True)

    async def handle(self) -> Any:
        captcha = EmojiCaptcha()
        await bot.send_photo(
            chat_id=self.event.chat.id,
            photo=BufferedInputFile(captcha.image, "captcha.jpeg"),
        )
