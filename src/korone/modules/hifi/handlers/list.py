from __future__ import annotations

from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import LinkPreviewOptions

from korone.modules.hifi.callbacks import HifiTracksPageCallback
from korone.modules.hifi.utils.formatters import build_search_results_text, clamp_page
from korone.modules.hifi.utils.keyboard import create_tracks_keyboard
from korone.modules.hifi.utils.session import get_search_session
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message


@flags.help(exclude=True)
class HifiTrackListCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (HifiTracksPageCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = cast("HifiTracksPageCallback", self.callback_data)

        if self.event.from_user.id != callback_data.user_id:
            await self.event.answer(_("You are not allowed to use this button."), show_alert=True)
            return

        search_session = await get_search_session(callback_data.token)
        if search_session is None:
            await self.event.answer(_("Search session expired. Please run /song again."), show_alert=True)
            return

        if not search_session.tracks:
            await self.event.answer(_("No tracks found."), show_alert=True)
            return

        page = clamp_page(callback_data.page, len(search_session.tracks))
        text = build_search_results_text(query=search_session.query, total_count=len(search_session.tracks), page=page)
        keyboard = create_tracks_keyboard(
            session=search_session, token=callback_data.token, page=page, user_id=callback_data.user_id
        )

        message = cast("Message", self.event.message)

        try:
            await message.edit_text(
                text, reply_markup=keyboard, link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
        except TelegramBadRequest as err:
            if "message is not modified" not in err.message:
                raise

        await self.event.answer()
