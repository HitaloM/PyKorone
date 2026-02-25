from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ass_tg.types import OptionalArg, WordArg

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.callbacks import LastFMAlbumRefreshCallback
from korone.modules.lastfm.handlers.common import (
    build_link_preview_options,
    can_use_buttons,
    format_missing_lastfm_username,
    resolve_lastfm_username,
    typing_action,
)
from korone.modules.lastfm.utils import (
    DeezerClient,
    DeezerError,
    LastFMAPIError,
    LastFMClient,
    LastFMError,
    format_album_status,
    format_lastfm_error,
)
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup, Message
    from ass_tg.types.base_abc import ArgFabric

    from korone.modules.lastfm.utils import LastFMAlbumInfo, LastFMRecentTrack


@dataclass(slots=True, frozen=True)
class LastFMAlbumPayload:
    username: str
    track: LastFMRecentTrack
    album_info: LastFMAlbumInfo | None
    deezer_image_url: str | None

    @property
    def text(self) -> str:
        return format_album_status(username=self.username, track=self.track, album_info=self.album_info)

    @property
    def image_url(self) -> str | None:
        if self.deezer_image_url:
            return self.deezer_image_url

        if self.album_info and self.album_info.image_url:
            return self.album_info.image_url
        return self.track.image_url


def _build_keyboard(*, username: str, owner_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔃", callback_data=LastFMAlbumRefreshCallback(u=username, uid=owner_id).pack())
    )
    return builder.as_markup()


async def _build_album_payload(
    client: LastFMClient, deezer_client: DeezerClient | None = None, *, username: str
) -> LastFMAlbumPayload | None:
    recent_tracks = await client.get_recent_tracks(username=username, limit=1)
    if not recent_tracks:
        return None

    track = recent_tracks[0]
    track_album = track.album
    if not track_album:
        return None

    album_info = None
    try:
        album_info = await client.get_album_info(username=username, artist=track.artist, album=track_album)
    except LastFMAPIError:
        album_info = None

    deezer_image_url = None
    if deezer_client:
        album_name = album_info.name if album_info else track_album
        artist_name = album_info.artist if album_info else track.artist
        try:
            deezer_image_url = await deezer_client.get_album_image(artist_name=artist_name, album_name=album_name)
        except DeezerError:
            deezer_image_url = None

    return LastFMAlbumPayload(username=username, track=track, album_info=album_info, deezer_image_url=deezer_image_url)


@flags.help(description=l_("Shows album info for your current Last.fm track."))
@flags.disableable(name="lfmalbum")
class LastFMAlbumHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"username": OptionalArg(WordArg(l_("Username")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("lfmalbum", "lalb")),)

    async def handle(self) -> None:
        explicit_username = str(self.data.get("username") or "").strip()
        username = await resolve_lastfm_username(self.event, explicit_username)

        if not username:
            await self.event.reply(format_missing_lastfm_username())
            return

        try:
            async with typing_action(bot=self.bot, message=self.event):
                client = LastFMClient()
                deezer_client = DeezerClient()
                payload = await _build_album_payload(client, deezer_client, username=username)
        except LastFMError as exc:
            await self.event.reply(format_lastfm_error(exc))
            return

        if payload is None:
            await self.event.reply(_("No album information found for the current track."))
            return

        owner_id = self.event.from_user.id if self.event.from_user else 0
        keyboard = _build_keyboard(username=username, owner_id=owner_id)
        link_preview_options = build_link_preview_options(payload.image_url)
        await self.event.reply(payload.text, reply_markup=keyboard, link_preview_options=link_preview_options)


@flags.help(exclude=True)
class LastFMAlbumCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return ()

    @classmethod
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, LastFMAlbumRefreshCallback.filter())

    async def _refresh(self, *, username: str, owner_id: int) -> None:
        message = cast("Message", self.event.message)
        client = LastFMClient()
        deezer_client = DeezerClient()
        payload = await _build_album_payload(client, deezer_client, username=username)
        if payload is None:
            await message.edit_text(_("No album information found for the current track."))
            return

        keyboard = _build_keyboard(username=username, owner_id=owner_id)
        link_preview_options = build_link_preview_options(payload.image_url)
        await message.edit_text(payload.text, reply_markup=keyboard, link_preview_options=link_preview_options)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = self.callback_data
        if not isinstance(callback_data, LastFMAlbumRefreshCallback):
            await self.event.answer()
            return

        username = callback_data.u
        owner_id = callback_data.uid

        if not can_use_buttons(callback_owner_id=owner_id, user_id=self.event.from_user.id):
            await self.event.answer(_("You are not allowed to use this button."), show_alert=True)
            return

        try:
            await self._refresh(username=username, owner_id=owner_id)
            await self.event.answer()
        except LastFMError as exc:
            await self.event.answer(format_lastfm_error(exc), show_alert=True)
        except TelegramBadRequest as exc:
            if "message is not modified" in exc.message.lower():
                await self.event.answer(_("No updates from your profile."))
                return
            raise
