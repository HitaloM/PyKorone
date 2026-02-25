from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import quote_plus

from aiogram import flags
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ass_tg.types import OptionalArg, TextArg
from stfu_tg import Template, Url

from korone.db.repositories.lastfm import LastFMRepository
from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.callbacks import LastFMCollageCallback
from korone.modules.lastfm.handlers.common import can_use_buttons, format_missing_lastfm_username, period_label
from korone.modules.lastfm.utils import LastFMClient, LastFMError, create_album_collage, format_lastfm_error
from korone.modules.lastfm.utils.collage import MAX_SIZE, MIN_SIZE, LastFMCollageError
from korone.modules.lastfm.utils.periods import LastFMPeriod, parse_period_token
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup, Message
    from ass_tg.types.base_abc import ArgFabric


COLLAGE_CLEAN_TOKENS = {"clean", "notext", "nonames"}


@dataclass(slots=True, frozen=True)
class LastFMCollageOptions:
    size: int = 3
    period: LastFMPeriod = LastFMPeriod.OVERALL
    include_text: bool = True


def _parse_size(token: str) -> int | None:
    fragment = token.split("x", 1)[0]
    if not fragment.isdigit():
        return None

    size = int(fragment)
    if MIN_SIZE <= size <= MAX_SIZE:
        return size
    return None


def _parse_options(raw_options: str) -> LastFMCollageOptions:
    options = LastFMCollageOptions()
    for token in raw_options.lower().split():
        if token in COLLAGE_CLEAN_TOKENS:
            options = LastFMCollageOptions(size=options.size, period=options.period, include_text=False)
            continue

        if parsed_size := _parse_size(token):
            options = LastFMCollageOptions(size=parsed_size, period=options.period, include_text=options.include_text)
            continue

        parsed_period = parse_period_token(token, default=options.period)
        if parsed_period != options.period:
            options = LastFMCollageOptions(size=options.size, period=parsed_period, include_text=options.include_text)

    return options


def _build_caption(*, username: str, options: LastFMCollageOptions) -> str:
    profile_url = f"https://www.last.fm/user/{quote_plus(username)}"
    return Template(
        _("{username}'s {period} album collage ({size}x{size})"),
        username=Url(username, profile_url),
        period=period_label(options.period),
        size=options.size,
    ).to_html()


def _build_keyboard(*, owner_id: int, target_id: int, options: LastFMCollageOptions) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    button_count = 0

    if options.size < MAX_SIZE:
        builder.button(
            text="➕",
            callback_data=LastFMCollageCallback(
                uid=owner_id, tid=target_id, s=options.size + 1, p=options.period, t=int(options.include_text)
            ),
        )
        button_count += 1

    if options.size > MIN_SIZE:
        builder.button(
            text="➖",
            callback_data=LastFMCollageCallback(
                uid=owner_id, tid=target_id, s=options.size - 1, p=options.period, t=int(options.include_text)
            ),
        )
        button_count += 1

    builder.button(
        text="Aa",
        callback_data=LastFMCollageCallback(
            uid=owner_id, tid=target_id, s=options.size, p=options.period, t=0 if options.include_text else 1
        ),
    )
    button_count += 1

    builder.adjust(button_count)
    return builder.as_markup()


async def _render_collage(*, username: str, options: LastFMCollageOptions) -> bytes:
    client = LastFMClient()
    albums = await client.get_top_albums(username=username, period=options.period.value, limit=100)
    if not albums:
        msg = _("No top albums found for this Last.fm user and period.")
        raise LastFMCollageError(msg)

    return await create_album_collage(albums=albums, size=options.size, include_text=options.include_text)


@flags.help(description=l_("Creates an album collage from Last.fm top albums."))
@flags.chat_action(action=ChatAction.UPLOAD_PHOTO, initial_sleep=0.2, interval=4.0)
@flags.disableable(name="lfmcollage")
class LastFMCollageHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"options": OptionalArg(TextArg(l_("Options")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("lfmcollage", "collage", "lcollage")),)

    async def _resolve_target_id(self) -> int | None:
        if self.event.reply_to_message and self.event.reply_to_message.from_user:
            return self.event.reply_to_message.from_user.id

        if self.event.from_user:
            return self.event.from_user.id

        return None

    async def handle(self) -> None:
        target_id = await self._resolve_target_id()
        if target_id is None:
            await self.event.reply(_("Could not identify the target user."))
            return

        username = await LastFMRepository.get_username(target_id)
        if not username:
            await self.event.reply(format_missing_lastfm_username())
            return

        raw_options = str(self.data.get("options") or "").strip()
        options = _parse_options(raw_options)

        try:
            image_bytes = await _render_collage(username=username, options=options)
            owner_id = self.event.from_user.id if self.event.from_user else 0
            keyboard = _build_keyboard(owner_id=owner_id, target_id=target_id, options=options)
            caption = _build_caption(username=username, options=options)

            await self.event.reply_photo(
                photo=BufferedInputFile(image_bytes, filename="lfm-collage.jpg"), caption=caption, reply_markup=keyboard
            )
        except LastFMError as exc:
            await self.event.reply(format_lastfm_error(exc))
            return
        except LastFMCollageError as exc:
            await self.event.reply(str(exc))
            return


@flags.help(exclude=True)
class LastFMCollageCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return ()

    @classmethod
    def register(cls, router: Router) -> None:
        router.callback_query.register(cls, LastFMCollageCallback.filter())

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = self.callback_data
        if not isinstance(callback_data, LastFMCollageCallback):
            await self.event.answer()
            return

        if not can_use_buttons(callback_owner_id=callback_data.uid, user_id=self.event.from_user.id):
            await self.event.answer(_("You are not allowed to use this button."), show_alert=True)
            return

        username = await LastFMRepository.get_username(callback_data.tid)
        if not username:
            await self.event.answer(_("Last.fm username not found for this user."), show_alert=True)
            return

        options = LastFMCollageOptions(size=callback_data.s, period=callback_data.p, include_text=bool(callback_data.t))

        message = cast("Message", self.event.message)
        try:
            image_bytes = await _render_collage(username=username, options=options)
            keyboard = _build_keyboard(owner_id=callback_data.uid, target_id=callback_data.tid, options=options)
            caption = _build_caption(username=username, options=options)
            await message.edit_media(
                media=InputMediaPhoto(
                    media=BufferedInputFile(image_bytes, filename="lfm-collage.jpg"), caption=caption
                ),
                reply_markup=keyboard,
            )
            await self.event.answer()
        except LastFMError as exc:
            await self.event.answer(format_lastfm_error(exc), show_alert=True)
        except LastFMCollageError as exc:
            await self.event.answer(str(exc), show_alert=True)
        except TelegramBadRequest as exc:
            if "message is not modified" in exc.message.lower():
                await self.event.answer(_("No updates from your profile."))
                return
            raise
