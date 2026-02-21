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
    download_cover_image,
    download_stream_audio,
    get_track_stream,
)
from korone.modules.hifi.utils.formatters import build_album_cover_url, build_track_caption, build_track_filename
from korone.modules.hifi.utils.session import can_request_track_in_chat, get_search_session
from korone.modules.utils_.file_id_cache import (
    delete_cached_file_payload,
    get_cached_file_payload,
    make_file_id_cache_key,
    set_cached_file_payload,
)
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message

    from korone.modules.hifi.utils.types import HifiTrack


@flags.help(exclude=True)
class HifiTrackDownloadCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (HifiTrackDownloadCallback.filter(),)

    @staticmethod
    async def _download_thumbnail(track: HifiTrack) -> BufferedInputFile | None:
        if not (cover_url := build_album_cover_url(track)):
            return None

        payload = await download_cover_image(cover_url)
        if payload is None:
            return None

        return BufferedInputFile(payload, filename=f"tidal-cover-{track.id}.jpg")

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
        can_request = await can_request_track_in_chat(message.chat.id, message.message_thread_id, track.id)
        if not can_request:
            await self.event.answer(_("This track has been requested recently in this chat."), show_alert=True)
            return
        cache_key = make_file_id_cache_key("hifi-track", f"{track.id}:LOSSLESS")

        await self.event.answer()

        cached_payload = await get_cached_file_payload(cache_key)
        cached_file_id = cached_payload.get("audio_file_id") if cached_payload else None
        cached_caption = cached_payload.get("caption") if cached_payload else None
        if isinstance(cached_file_id, str) and cached_file_id:
            try:
                await message.reply_audio(
                    audio=cached_file_id,
                    caption=cached_caption if isinstance(cached_caption, str) else None,
                    title=track.title,
                    performer=track.artist,
                    duration=track.duration,
                )
            except TelegramBadRequest:
                await delete_cached_file_payload(cache_key)
            else:
                return

        try:
            stream = await get_track_stream(track.id, preferred_quality="LOSSLESS")
        except HifiStreamUnavailableError:
            await message.reply(_("Could not get an audio stream for this track."))
            return
        except HifiAPIError:
            await message.reply(_("Could not fetch track information right now."))
            return

        try:
            async with ChatActionSender.upload_document(
                chat_id=message.chat.id, bot=self.bot, message_thread_id=message.message_thread_id
            ):
                payload, content_type = await download_stream_audio(stream)
                audio = BufferedInputFile(payload, filename=build_track_filename(track, stream, content_type))
                thumbnail = await self._download_thumbnail(track)

                caption = build_track_caption(track, stream)
                sent_message = await message.reply_audio(
                    audio=audio,
                    caption=caption,
                    title=track.title,
                    performer=track.artist,
                    duration=track.duration,
                    thumbnail=thumbnail,
                )

                if sent_message.audio:
                    await set_cached_file_payload(
                        cache_key, {"audio_file_id": sent_message.audio.file_id, "caption": caption}
                    )
        except HifiTrackTooLargeError:
            await message.reply(_("This track is too large to send on Telegram."))
            return
        except HifiAPIError:
            await message.reply(_("Could not download this track right now."))
            return
        except TelegramBadRequest:
            await message.reply(_("Could not send this track right now."))
