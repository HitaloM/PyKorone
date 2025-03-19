from typing import Optional

from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)

from sophie_bot.modules.welcomesecurity.utils_.emoji_captcha import EmojiCaptcha
from sophie_bot.services.bot import bot


async def send_captcha_message(
    message: Message, captcha: EmojiCaptcha, caption: str, reply_markup: Optional[InlineKeyboardMarkup] = None
):
    return await bot.edit_message_media(
        media=InputMediaPhoto(media=BufferedInputFile(captcha.image, "captcha.jpeg"), caption=caption),
        chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=reply_markup,
    )
