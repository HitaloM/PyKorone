from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from aiogram import flags
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.modules.lastfm.callbacks import LastFMArtistRefreshCallback
from korone.modules.lastfm.handlers.base import BaseLastFMCallbackHandler, BaseLastFMMessageHandler, LastFMUserContext
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
    user: LastFMUserContext
    track: LastFMRecentTrack
    artist_info: LastFMArtistInfo | None
    image_url: str | None

    @property
    def text(self) -> str:
        return format_artist_status(
            username=self.user.username,
            display_name=self.user.display_name,
            track=self.track,
            artist_info=self.artist_info,
        )


class LastFMArtistView:
    @classmethod
    async def build_payload_from_track(
        cls, *, user: LastFMUserContext, track: LastFMRecentTrack
    ) -> LastFMArtistPayload:
        client = LastFMClient()
        deezer_client = DeezerClient()
        artist_info = None
        try:
            artist_info = await client.get_artist_info(username=user.username, artist=track.artist)
        except LastFMAPIError:
            artist_info = None

        image_url = None
        artist_name = artist_info.name if artist_info else track.artist
        try:
            image_url = await deezer_client.get_artist_image(artist_name)
        except DeezerError:
            image_url = None

        return LastFMArtistPayload(user=user, track=track, artist_info=artist_info, image_url=image_url)

    @classmethod
    async def build_payload_for_user(cls, *, user: LastFMUserContext) -> LastFMArtistPayload | None:
        client = LastFMClient()
        recent_tracks = await client.get_recent_tracks(username=user.username, limit=1)
        if not recent_tracks:
            return None
        return await cls.build_payload_from_track(user=user, track=recent_tracks[0])

    @classmethod
    def empty_state_text(cls) -> str:
        return _("No artist information found for the current track.")

    @classmethod
    def build_reply_markup_for_user(
        cls, *, user: LastFMUserContext, payload: LastFMArtistPayload
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔃", callback_data=LastFMArtistRefreshCallback(u=user.username, uid=user.telegram_user_id))
        return builder.as_markup()


@flags.help(description=l_("Show artist details for the current Last.fm track."))
@flags.chat_action(action=ChatAction.TYPING, initial_sleep=0.7)
@flags.disableable(name="lfmartist")
class LastFMArtistHandler(LastFMArtistView, BaseLastFMMessageHandler[LastFMArtistPayload]):
    @classmethod
    @override
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("lfmartist", "lart"),)


@flags.help(exclude=True)
class LastFMArtistCallbackHandler(LastFMArtistView, BaseLastFMCallbackHandler[LastFMUserContext, LastFMArtistPayload]):
    @classmethod
    @override
    def filters(cls) -> tuple[CallbackType, ...]:
        return ()

    @classmethod
    @override
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, LastFMArtistRefreshCallback.filter())

    @override
    async def resolve_context(self) -> LastFMUserContext | None:
        callback_data = self.callback_data
        if not isinstance(callback_data, LastFMArtistRefreshCallback):
            return None

        owner_id = callback_data.uid
        username = await self.resolve_username_for_user(owner_id) or callback_data.u
        return LastFMUserContext(
            username=username, display_name=self.event.from_user.first_name, telegram_user_id=owner_id
        )
