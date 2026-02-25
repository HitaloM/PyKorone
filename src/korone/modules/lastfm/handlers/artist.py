from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ass_tg.types import OptionalArg, WordArg

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.callbacks import LastFMArtistRefreshCallback
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
    format_artist_status,
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


def _build_keyboard(*, username: str, owner_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔃", callback_data=LastFMArtistRefreshCallback(u=username, uid=owner_id).pack())
    )
    return builder.as_markup()


async def _build_artist_payload(
    client: LastFMClient, deezer_client: DeezerClient, *, username: str
) -> LastFMArtistPayload | None:
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


@flags.help(description=l_("Shows artist info for your current Last.fm track."))
@flags.disableable(name="lfmartist")
class LastFMArtistHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"username": OptionalArg(WordArg(l_("Username")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("lfmartist", "lart")),)

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
                payload = await _build_artist_payload(client, deezer_client, username=username)
        except LastFMError as exc:
            await self.event.reply(format_lastfm_error(exc))
            return

        if payload is None:
            await self.event.reply(_("No artist information found for the current track."))
            return

        owner_id = self.event.from_user.id if self.event.from_user else 0
        keyboard = _build_keyboard(username=username, owner_id=owner_id)
        link_preview_options = build_link_preview_options(payload.image_url)
        await self.event.reply(payload.text, reply_markup=keyboard, link_preview_options=link_preview_options)


@flags.help(exclude=True)
class LastFMArtistCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return ()

    @classmethod
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, LastFMArtistRefreshCallback.filter())

    async def _refresh(self, *, username: str, owner_id: int) -> None:
        message = cast("Message", self.event.message)
        client = LastFMClient()
        deezer_client = DeezerClient()
        payload = await _build_artist_payload(client, deezer_client, username=username)
        if payload is None:
            await message.edit_text(_("No artist information found for the current track."))
            return

        keyboard = _build_keyboard(username=username, owner_id=owner_id)
        link_preview_options = build_link_preview_options(payload.image_url)
        await message.edit_text(payload.text, reply_markup=keyboard, link_preview_options=link_preview_options)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = self.callback_data
        if not isinstance(callback_data, LastFMArtistRefreshCallback):
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
