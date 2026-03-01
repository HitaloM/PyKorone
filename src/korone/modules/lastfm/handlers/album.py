from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from aiogram import flags
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.modules.lastfm.callbacks import LastFMAlbumRefreshCallback
from korone.modules.lastfm.handlers.base import (
    BaseLastFMCallbackHandler,
    BaseLastFMMessageHandler,
    LastFMCallbackContext,
)
from korone.modules.lastfm.utils import DeezerClient, DeezerError, LastFMAPIError, LastFMClient, format_album_status
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup

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


class LastFMAlbumView:
    @classmethod
    async def build_payload_for_username(cls, *, username: str) -> LastFMAlbumPayload | None:
        client = LastFMClient()
        deezer_client = DeezerClient()
        recent_tracks = await client.get_recent_tracks(username=username, limit=1)
        if not recent_tracks:
            return None

        track = recent_tracks[0]
        if not track.album:
            return None

        album_info = None
        try:
            album_info = await client.get_album_info(username=username, artist=track.artist, album=track.album)
        except LastFMAPIError:
            album_info = None

        deezer_image_url = None
        album_name = album_info.name if album_info else track.album
        artist_name = album_info.artist if album_info else track.artist
        try:
            deezer_image_url = await deezer_client.get_album_image(artist_name=artist_name, album_name=album_name)
        except DeezerError:
            deezer_image_url = None

        return LastFMAlbumPayload(
            username=username, track=track, album_info=album_info, deezer_image_url=deezer_image_url
        )

    @classmethod
    def empty_state_text(cls) -> str:
        return _("No album information found for the current track.")

    @classmethod
    def build_reply_markup_for_owner(
        cls, *, username: str, owner_id: int, payload: LastFMAlbumPayload
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔃", callback_data=LastFMAlbumRefreshCallback(u=username, uid=owner_id))
        return builder.as_markup()


@flags.help(description=l_("Show album details for the current Last.fm track."))
@flags.chat_action(action=ChatAction.TYPING, initial_sleep=0.7)
@flags.disableable(name="lfmalbum")
class LastFMAlbumHandler(LastFMAlbumView, BaseLastFMMessageHandler[LastFMAlbumPayload]):
    @staticmethod
    @override
    def filters() -> tuple[CallbackType, ...]:
        return (Command("lfmalbum", "lalb"),)


@flags.help(exclude=True)
class LastFMAlbumCallbackHandler(LastFMAlbumView, BaseLastFMCallbackHandler[LastFMCallbackContext, LastFMAlbumPayload]):
    @staticmethod
    @override
    def filters() -> tuple[CallbackType, ...]:
        return ()

    @classmethod
    @override
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, LastFMAlbumRefreshCallback.filter())

    @override
    async def resolve_context(self) -> LastFMCallbackContext | None:
        callback_data = self.callback_data
        if not isinstance(callback_data, LastFMAlbumRefreshCallback):
            return None

        owner_id = callback_data.uid
        username = await self.resolve_username_for_user(owner_id) or callback_data.u
        return LastFMCallbackContext(username=username, owner_id=owner_id)
