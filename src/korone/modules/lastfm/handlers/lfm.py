from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from aiogram import flags
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.modules.lastfm.callbacks import LastFMMode, LastFMRefreshCallback, LastFMViewCallback
from korone.modules.lastfm.handlers.base import (
    BaseLastFMCallbackHandler,
    BaseLastFMMessageHandler,
    LastFMCallbackContext,
)
from korone.modules.lastfm.utils import DeezerClient, DeezerError, LastFMAPIError, LastFMClient, format_status
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup

    from korone.modules.lastfm.utils import LastFMRecentTrack, LastFMTrackInfo


@dataclass(slots=True, frozen=True)
class LastFMStatusPayload:
    mode: LastFMMode
    username: str
    image_url: str | None
    tracks: list[LastFMRecentTrack]
    track_info: LastFMTrackInfo | None

    @property
    def text(self) -> str:
        return format_status(username=self.username, tracks=self.tracks, track_info=self.track_info)


@dataclass(slots=True, frozen=True)
class LastFMStatusCallbackContext(LastFMCallbackContext):
    mode: LastFMMode


class LastFMStatusView:
    @classmethod
    def track_limit(cls, mode: LastFMMode) -> int:
        return 4 if mode is LastFMMode.EXPANDED else 1

    @classmethod
    async def build_status_payload(cls, *, username: str, mode: LastFMMode) -> LastFMStatusPayload | None:
        client = LastFMClient()
        deezer_client = DeezerClient()
        tracks = await client.get_recent_tracks(username=username, limit=cls.track_limit(mode))
        if not tracks:
            return None

        first_track = tracks[0]
        visible_tracks = tracks if mode is LastFMMode.EXPANDED else tracks[:1]

        track_info = None
        try:
            track_info = await client.get_track_info(
                username=username, artist=first_track.artist, track=first_track.name
            )
        except LastFMAPIError:
            track_info = None

        image_url = first_track.image_url
        try:
            deezer_image_url = await deezer_client.get_track_image(
                artist_name=first_track.artist, track_name=first_track.name, album_name=first_track.album
            )
        except DeezerError:
            deezer_image_url = None

        if deezer_image_url:
            image_url = deezer_image_url

        return LastFMStatusPayload(
            mode=mode, username=username, image_url=image_url, tracks=visible_tracks, track_info=track_info
        )

    @classmethod
    async def build_payload_for_username(cls, *, username: str) -> LastFMStatusPayload | None:
        return await cls.build_status_payload(username=username, mode=LastFMMode.COMPACT)

    @classmethod
    async def build_payload(cls, *, context: LastFMStatusCallbackContext) -> LastFMStatusPayload | None:
        return await cls.build_status_payload(username=context.username, mode=context.mode)

    @classmethod
    def empty_state_text(cls) -> str:
        return _("No scrobbles found for this Last.fm user.")

    @classmethod
    def build_reply_markup_for_owner(
        cls, *, username: str, owner_id: int, payload: LastFMStatusPayload
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        if payload.mode is LastFMMode.EXPANDED:
            builder.button(text="➖", callback_data=LastFMViewCallback(u=username, m=LastFMMode.COMPACT, uid=owner_id))
        else:
            builder.button(text="➕", callback_data=LastFMViewCallback(u=username, m=LastFMMode.EXPANDED, uid=owner_id))

        builder.button(text="🔃", callback_data=LastFMRefreshCallback(u=username, m=payload.mode, uid=owner_id))
        builder.adjust(2)
        return builder.as_markup()


@flags.help(description=l_("Show the current Last.fm listening status."))
@flags.chat_action(action=ChatAction.TYPING, initial_sleep=0.7)
@flags.disableable(name="lastfm")
class LastFMStatusHandler(LastFMStatusView, BaseLastFMMessageHandler[LastFMStatusPayload]):
    @staticmethod
    @override
    def filters() -> tuple[CallbackType, ...]:
        return (Command("lfm", "lastfm", "lmu", "np"),)


@flags.help(exclude=True)
class LastFMStatusCallbackHandler(
    LastFMStatusView, BaseLastFMCallbackHandler[LastFMStatusCallbackContext, LastFMStatusPayload]
):
    @staticmethod
    @override
    def filters() -> tuple[CallbackType, ...]:
        return ()

    @classmethod
    @override
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, LastFMViewCallback.filter())
        router.callback_query.register(cls, LastFMRefreshCallback.filter())

    @override
    async def resolve_context(self) -> LastFMStatusCallbackContext | None:
        callback_data = self.callback_data
        if not isinstance(callback_data, (LastFMViewCallback, LastFMRefreshCallback)):
            return None

        owner_id = callback_data.uid
        username = await self.resolve_username_for_user(owner_id) or callback_data.u
        return LastFMStatusCallbackContext(username=username, owner_id=owner_id, mode=callback_data.m)

    @override
    async def handle_not_modified(self) -> None:
        await self.event.answer()
