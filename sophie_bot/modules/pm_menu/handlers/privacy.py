from typing import Any

from aiogram.handlers import MessageHandler
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from sophie_bot import CONFIG
from sophie_bot.utils.i18n import gettext as _


class PrivacyInfo(MessageHandler):
    async def handle(self) -> Any:
        text = _("The privacy policy of the bot is available on our wiki page.")
        buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_("Privacy Policy"),
                        url=CONFIG.privacy_link,
                    )
                ]
            ]
        )

        await self.event.reply(text, reply_markup=buttons)
