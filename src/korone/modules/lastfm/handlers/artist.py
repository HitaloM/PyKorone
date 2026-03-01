from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from aiogram import flags
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.modules.lastfm.callbacks import LastFMArtistRefreshCallback
from korone.modules.lastfm.handlers.base import (
    BaseLastFMCallbackHandler,
    BaseLastFMMessageHandler,
    LastFMCallbackContext,
)
from korone.modules.lastfm.utils import DeezerClient, DeezerError, LastFMAPIError, LastFMClient, format_artist_status
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup

    from korone.modules.lastfm.utils import LastFMArtistInfo, LastFMRecentTrack


@dataclass(slots=True, frozen=True)
class LastFMArtistPayload:
    username: str
    track: LastFMRecentTrack
    artist_info: LastFMArtistInfo | None
    image_url: str | None

    @property
    def text(self) -> str:
        return format_artist_status(username=self.username, track=self.track, artist_info=self.artist_info)


class LastFMArtistView:
    @classmethod
    async def build_payload_for_username(cls, *, username: str) -> LastFMArtistPayload | None:
        client = LastFMClient()
        deezer_client = DeezerClient()
        recent_tracks = await client.get_recent_tracks(username=username, limit=1)
        if not recent_tracks:
            return None

        track = recent_tracks[0]
        artist_info = None
        try:
            artist_info = await client.get_artist_info(username=username, artist=track.artist)
        except LastFMAPIError:
            artist_info = None

        image_url = None
        artist_name = artist_info.name if artist_info else track.artist
        try:
            image_url = await deezer_client.get_artist_image(artist_name)
        except DeezerError:
            image_url = None

        return LastFMArtistPayload(username=username, track=track, artist_info=artist_info, image_url=image_url)

    @classmethod
    def empty_state_text(cls) -> str:
        return _("No artist information found for the current track.")

    @classmethod
    def build_reply_markup_for_owner(
        cls, *, username: str, owner_id: int, payload: LastFMArtistPayload
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔃", callback_data=LastFMArtistRefreshCallback(u=username, uid=owner_id))
        return builder.as_markup()


@flags.help(description=l_("Show artist details for the current Last.fm track."))
@flags.chat_action(action=ChatAction.TYPING, initial_sleep=0.7)
@flags.disableable(name="lfmartist")
class LastFMArtistHandler(LastFMArtistView, BaseLastFMMessageHandler[LastFMArtistPayload]):
    @staticmethod
    @override
    def filters() -> tuple[CallbackType, ...]:
        return (Command("lfmartist", "lart"),)


@flags.help(exclude=True)
class LastFMArtistCallbackHandler(
    LastFMArtistView, BaseLastFMCallbackHandler[LastFMCallbackContext, LastFMArtistPayload]
):
    @staticmethod
    @override
    def filters() -> tuple[CallbackType, ...]:
        return ()

    @classmethod
    @override
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, LastFMArtistRefreshCallback.filter())

    @override
    async def resolve_context(self) -> LastFMCallbackContext | None:
        callback_data = self.callback_data
        if not isinstance(callback_data, LastFMArtistRefreshCallback):
            return None

        owner_id = callback_data.uid
        username = await self.resolve_username_for_user(owner_id) or callback_data.u
        return LastFMCallbackContext(username=username, owner_id=owner_id)
