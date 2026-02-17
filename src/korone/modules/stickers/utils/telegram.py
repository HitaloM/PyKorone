from typing import TYPE_CHECKING

from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.exceptions import TelegramBadRequest


def bad_request_text(error: TelegramBadRequest) -> str:
    error_message = getattr(error, "message", None)
    if error_message:
        return str(error_message).lower()
    return str(error).lower()


def is_stickerset_invalid(error: TelegramBadRequest) -> bool:
    text = bad_request_text(error)
    return "stickerset_invalid" in text or "sticker set not found" in text


def is_pack_full_error(error: TelegramBadRequest) -> bool:
    text = bad_request_text(error)
    return "stickers_too_much" in text or "sticker set is full" in text


def map_pack_write_error(error: TelegramBadRequest) -> str:
    text = bad_request_text(error)

    if "invalid sticker emojis" in text or "sticker_emoji_invalid" in text:
        return _("Invalid emoji provided.")
    if "sticker set name invalid" in text:
        return _("Invalid pack name.")
    if "sticker set name is already occupied" in text:
        return _("That pack ID already exists and cannot be reused.")
    if "sticker_tgs_notgs" in text:
        return _("Animated sticker cannot be added to a non-animated pack.")
    if "sticker_png_nopng" in text:
        return _("Static sticker cannot be added to an animated pack.")
    if "stickers_too_much" in text:
        return _("Sticker pack limit exceeded.")
    if "peer_id_invalid" in text:
        return _("I cannot create a sticker pack for you yet. Start the bot in private first.")
    return _("Could not save the sticker due to a Telegram API error.")
