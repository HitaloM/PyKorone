from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import LinkPreviewOptions
from stfu_tg import Code, Template

from korone.db.repositories.lastfm import LastFMRepository
from korone.modules.lastfm.utils.periods import LastFMPeriod
from korone.modules.utils_.message import is_real_reply
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import Message


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


def build_link_preview_options(image_url: str | None) -> LinkPreviewOptions | None:
    if not image_url:
        return None

    return LinkPreviewOptions(is_disabled=False, url=image_url, prefer_large_media=True, show_above_text=True)
