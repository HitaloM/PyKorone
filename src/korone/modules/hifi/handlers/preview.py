from __future__ import annotations

from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions

from korone.modules.hifi.callbacks import HifiTrackDownloadCallback, HifiTrackSendCallback, HifiTracksPageCallback
from korone.modules.hifi.utils.formatters import build_album_cover_url, build_track_preview_text
from korone.modules.hifi.utils.session import get_search_session
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message


@flags.help(exclude=True)
class HifiTrackPreviewCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (HifiTrackSendCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = cast("HifiTrackSendCallback", self.callback_data)

        search_session = await get_search_session(callback_data.token)
        if search_session is None:
            await self.event.answer(_("Search session expired. Please run /song again."), show_alert=True)
            return

        if self.event.from_user.id != search_session.user_id:
            await self.event.answer(_("You are not allowed to use this button."), show_alert=True)
            return

        if callback_data.index < 0 or callback_data.index >= len(search_session.tracks):
            await self.event.answer(_("Invalid track selected."), show_alert=True)
            return

        track = search_session.tracks[callback_data.index]
        text = build_track_preview_text(track)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_("⬇️ Download"),
                        callback_data=HifiTrackDownloadCallback(
                            token=callback_data.token, index=callback_data.index, user_id=search_session.user_id
                        ).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=_("⬅️ Back"),
                        callback_data=HifiTracksPageCallback(
                            token=callback_data.token, page=callback_data.page, user_id=search_session.user_id
                        ).pack(),
                    )
                ],
            ]
        )

        cover_url = build_album_cover_url(track)
        link_preview_options = (
            LinkPreviewOptions(is_disabled=False, url=cover_url, prefer_large_media=True, show_above_text=True)
            if cover_url
            else LinkPreviewOptions(is_disabled=True)
        )

        message = cast("Message", self.event.message)
        try:
            await message.edit_text(text, reply_markup=keyboard, link_preview_options=link_preview_options)
        except TelegramBadRequest as err:
            if "message is not modified" not in err.message:
                raise

        await self.event.answer()
