from typing import TYPE_CHECKING

from korone.utils.i18n import gettext as _
from korone.utils.telegram_errors import normalized_error_message

if TYPE_CHECKING:
    from aiogram.exceptions import TelegramBadRequest


def is_stickerset_invalid(error: TelegramBadRequest) -> bool:
    text = normalized_error_message(error)
    return "stickerset invalid" in text or "sticker set not found" in text


def is_pack_full_error(error: TelegramBadRequest) -> bool:
    text = normalized_error_message(error)
    return "stickers too much" in text or "sticker set is full" in text


def map_pack_write_error(error: TelegramBadRequest) -> str:
    text = normalized_error_message(error)

    if "invalid sticker emojis" in text or "sticker emoji invalid" in text:
        return _("Invalid emoji provided.")
    if "sticker set name invalid" in text:
        return _("Invalid pack name.")
    if "sticker set name is already occupied" in text:
        return _("That pack ID already exists and cannot be reused.")
    if "sticker tgs notgs" in text:
        return _("Animated sticker cannot be added to a non-animated pack.")
    if "sticker png nopng" in text:
        return _("Static sticker cannot be added to an animated pack.")
    if "stickers too much" in text:
        return _("Sticker pack limit exceeded.")
    if "peer id invalid" in text:
        return _("I cannot create a sticker pack for you yet. Start the bot in private first.")
    return _("Could not save the sticker due to a Telegram API error.")
