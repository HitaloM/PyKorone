from __future__ import annotations

from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile
from aiogram.utils.chat_action import ChatActionSender

from korone.modules.hifi.callbacks import HifiTrackDownloadCallback
from korone.modules.hifi.utils.client import (
    HifiAPIError,
    HifiStreamUnavailableError,
    HifiTrackTooLargeError,
    download_stream_audio,
    get_track_stream,
)
from korone.modules.hifi.utils.formatters import build_track_caption, build_track_filename
from korone.modules.hifi.utils.session import get_search_session
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message


@flags.help(exclude=True)
class HifiTrackDownloadCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (HifiTrackDownloadCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = cast("HifiTrackDownloadCallback", self.callback_data)

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

        message = cast("Message", self.event.message)
        track = search_session.tracks[callback_data.index]

        await self.event.answer()

        try:
            stream = await get_track_stream(track.id, preferred_quality="LOSSLESS")
        except HifiStreamUnavailableError:
            await message.reply(_("Could not get an audio stream for this track."))
            return
        except HifiAPIError:
            await message.reply(_("Could not fetch track information right now."))
            return

        try:
            async with ChatActionSender.upload_document(chat_id=message.chat.id, bot=self.bot):
                payload, content_type = await download_stream_audio(stream)
                audio = BufferedInputFile(payload, filename=build_track_filename(track, stream, content_type))
                await message.reply_audio(
                    audio=audio, caption=build_track_caption(track, stream), title=track.title, performer=track.artist
                )
        except HifiTrackTooLargeError:
            await message.reply(_("This track is too large to send on Telegram."))
            return
        except HifiAPIError:
            await message.reply(_("Could not download this track right now."))
            return
        except TelegramBadRequest:
            await message.reply(_("Could not send this track right now."))
