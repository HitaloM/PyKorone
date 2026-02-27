from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from aiogram import flags
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ass_tg.types import OptionalArg, WordArg

from korone.modules.lastfm.callbacks import LastFMMode, LastFMRefreshCallback, LastFMViewCallback
from korone.modules.lastfm.handlers.common import (
    can_use_buttons,
    edit_lastfm_response,
    format_missing_lastfm_username,
    resolve_lastfm_username,
    send_lastfm_response,
)
from korone.modules.lastfm.utils import (
    DeezerClient,
    DeezerError,
    LastFMAPIError,
    LastFMClient,
    LastFMError,
    format_lastfm_error,
    format_status,
)
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup, Message
    from ass_tg.types.base_abc import ArgFabric

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


def _build_keyboard(*, username: str, mode: LastFMMode, owner_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if mode is LastFMMode.EXPANDED:
        builder.button(text="➖", callback_data=LastFMViewCallback(u=username, m=LastFMMode.COMPACT, uid=owner_id))
    else:
        builder.button(text="➕", callback_data=LastFMViewCallback(u=username, m=LastFMMode.EXPANDED, uid=owner_id))

    builder.button(text="🔃", callback_data=LastFMRefreshCallback(u=username, m=mode, uid=owner_id))

    builder.adjust(2)
    return builder.as_markup()


def _mode_track_limit(mode: LastFMMode) -> int:
    return 4 if mode is LastFMMode.EXPANDED else 1


async def _build_status_payload(
    client: LastFMClient, deezer_client: DeezerClient, *, username: str, mode: LastFMMode
) -> LastFMStatusPayload | None:
    tracks = await client.get_recent_tracks(username=username, limit=_mode_track_limit(mode))
    if not tracks:
        return None

    first_track = tracks[0]
    visible_tracks = tracks[:1] if mode is not LastFMMode.EXPANDED else tracks

    track_info = None
    try:
        track_info = await client.get_track_info(username=username, artist=first_track.artist, track=first_track.name)
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


async def _edit_status_message(message: Message, *, payload: LastFMStatusPayload, owner_id: int) -> None:
    keyboard = _build_keyboard(username=payload.username, mode=payload.mode, owner_id=owner_id)

    try:
        await edit_lastfm_response(message, text=payload.text, image_url=payload.image_url, reply_markup=keyboard)
    except TelegramBadRequest as err:
        if "message is not modified" in err.message.lower():
            return
        raise


@flags.help(description=l_("Show the current Last.fm listening status."))
@flags.chat_action(action=ChatAction.TYPING, initial_sleep=0.7)
@flags.disableable(name="lastfm")
class LastFMStatusHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"username": OptionalArg(WordArg(l_("Username")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("lfm", "lastfm", "lmu", "np"),)

    async def handle(self) -> None:
        explicit_username = str(self.data.get("username") or "").strip()
        username = await resolve_lastfm_username(self.event, explicit_username)

        if not username:
            await self.event.reply(format_missing_lastfm_username())
            return

        try:
            client = LastFMClient()
            deezer_client = DeezerClient()
            payload = await _build_status_payload(client, deezer_client, username=username, mode=LastFMMode.COMPACT)
        except LastFMError as exc:
            await self.event.reply(format_lastfm_error(exc))
            return

        if payload is None:
            await self.event.reply(_("No scrobbles found for this Last.fm user."))
            return

        owner_id = self.event.from_user.id if self.event.from_user else 0
        keyboard = _build_keyboard(username=username, mode=payload.mode, owner_id=owner_id)
        await send_lastfm_response(self.event, text=payload.text, image_url=payload.image_url, reply_markup=keyboard)


@flags.help(exclude=True)
class LastFMStatusCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return ()

    @classmethod
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, LastFMViewCallback.filter())
        router.callback_query.register(cls, LastFMRefreshCallback.filter())

    async def _refresh_or_change_view(self, *, username: str, mode: LastFMMode, owner_id: int) -> None:
        message = cast("Message", self.event.message)
        client = LastFMClient()
        deezer_client = DeezerClient()
        payload = await _build_status_payload(client, deezer_client, username=username, mode=mode)
        if payload is None:
            await message.edit_text(_("No scrobbles found for this Last.fm user."))
            return

        await _edit_status_message(message, payload=payload, owner_id=owner_id)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = self.callback_data
        if not isinstance(callback_data, (LastFMViewCallback, LastFMRefreshCallback)):
            await self.event.answer()
            return

        owner_id = callback_data.uid
        username = callback_data.u
        mode = callback_data.m

        if not can_use_buttons(callback_owner_id=owner_id, user_id=self.event.from_user.id):
            await self.event.answer(_("You are not allowed to use this button."), show_alert=True)
            return

        try:
            await self._refresh_or_change_view(username=username, mode=mode, owner_id=owner_id)
            await self.event.answer()
        except LastFMError as exc:
            await self.event.answer(format_lastfm_error(exc), show_alert=True)
        except TelegramBadRequest as exc:
            if "message is not modified" in exc.message.lower():
                await self.event.answer(_("No updates from your profile."))
                return
            raise
