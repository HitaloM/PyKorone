from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import InputMediaPhoto
from stfu_tg import Code, Template

from korone.db.repositories.lastfm import LastFMRepository
from korone.modules.lastfm.utils.periods import LastFMPeriod
from korone.modules.utils_.message import is_real_reply
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup, Message

LASTFM_FALLBACK_IMAGE_URL = "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png"


def can_use_buttons(*, callback_owner_id: int, user_id: int) -> bool:
    return callback_owner_id in {0, user_id}


async def resolve_lastfm_username(message: Message, explicit_username: str | None) -> str | None:
    if explicit_username:
        return explicit_username

    if message.reply_to_message and is_real_reply(message) and message.reply_to_message.from_user:
        return await LastFMRepository.get_username(message.reply_to_message.from_user.id)

    if message.from_user:
        return await LastFMRepository.get_username(message.from_user.id)

    return None


def format_missing_lastfm_username() -> str:
    return Template(_("Last.fm username not found. Use {example}."), example=Code("/setlfm your_username")).to_html()


def period_label(period: LastFMPeriod) -> str:
    if period is LastFMPeriod.ONE_WEEK:
        return _("1 week")
    if period is LastFMPeriod.ONE_MONTH:
        return _("1 month")
    if period is LastFMPeriod.THREE_MONTHS:
        return _("3 months")
    if period is LastFMPeriod.SIX_MONTHS:
        return _("6 months")
    if period is LastFMPeriod.ONE_YEAR:
        return _("1 year")
    return _("all-time")


def resolve_lastfm_image_url(image_url: str | None) -> str:
    return image_url or LASTFM_FALLBACK_IMAGE_URL


async def send_lastfm_response(
    message: Message, *, text: str, image_url: str | None, reply_markup: InlineKeyboardMarkup | None = None
) -> Message:
    return await message.reply_photo(photo=resolve_lastfm_image_url(image_url), caption=text, reply_markup=reply_markup)


async def edit_lastfm_response(
    message: Message, *, text: str, image_url: str | None, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    if not message.photo:
        await message.edit_text(text, reply_markup=reply_markup)
        return

    await message.edit_media(
        media=InputMediaPhoto(media=resolve_lastfm_image_url(image_url), caption=text), reply_markup=reply_markup
    )
