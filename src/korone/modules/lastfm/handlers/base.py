from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast, override

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputMediaPhoto
from stfu_tg import Code, Template

from korone.db.repositories.lastfm import LastFMRepository
from korone.modules.lastfm.utils import LastFMError, format_lastfm_error
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup, Message

LASTFM_FALLBACK_IMAGE_URL = "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png"


class LastFMResponsePayload(Protocol):
    @property
    def text(self) -> str: ...

    @property
    def image_url(self) -> str | None: ...


@dataclass(slots=True, frozen=True)
class LastFMCallbackContext:
    username: str
    owner_id: int


class LastFMHandlerSupport:
    @staticmethod
    def can_use_buttons(*, callback_owner_id: int, user_id: int) -> bool:
        return callback_owner_id in {0, user_id}

    @staticmethod
    async def resolve_username_for_user(user_id: int | None) -> str | None:
        if not user_id:
            return None

        return await LastFMRepository.get_username(user_id)

    @classmethod
    async def resolve_username_from_message(cls, message: Message) -> str | None:
        if not message.from_user:
            return None

        return await cls.resolve_username_for_user(message.from_user.id)

    @staticmethod
    def missing_username_text() -> str:
        return str(Template(_("Last.fm username not found. Use {example}."), example=Code("/setlfm your_username")))

    @staticmethod
    def resolve_image_url(image_url: str | None) -> str:
        return image_url or LASTFM_FALLBACK_IMAGE_URL

    @classmethod
    async def send_response(
        cls, message: Message, *, text: str, image_url: str | None, reply_markup: InlineKeyboardMarkup | None = None
    ) -> Message:
        return await message.reply_photo(
            photo=cls.resolve_image_url(image_url), caption=text, reply_markup=reply_markup
        )

    @classmethod
    async def edit_response(
        cls, message: Message, *, text: str, image_url: str | None, reply_markup: InlineKeyboardMarkup | None = None
    ) -> None:
        if not message.photo:
            await message.edit_text(text, reply_markup=reply_markup)
            return

        await message.edit_media(
            media=InputMediaPhoto(media=cls.resolve_image_url(image_url), caption=text), reply_markup=reply_markup
        )


class BaseLastFMMessageHandler[P: LastFMResponsePayload](KoroneMessageHandler, LastFMHandlerSupport):
    async def resolve_username(self) -> str | None:
        return await type(self).resolve_username_from_message(self.event)

    @classmethod
    @abstractmethod
    async def build_payload_for_username(cls, *, username: str) -> P | None:
        pass

    @classmethod
    @abstractmethod
    def empty_state_text(cls) -> str:
        pass

    @classmethod
    def build_reply_markup_for_owner(cls, *, username: str, owner_id: int, payload: P) -> InlineKeyboardMarkup | None:
        return None

    @override
    async def handle(self) -> None:
        username = await self.resolve_username()
        if not username:
            await self.event.reply(type(self).missing_username_text())
            return

        try:
            payload = await type(self).build_payload_for_username(username=username)
        except LastFMError as exc:
            await self.event.reply(format_lastfm_error(exc))
            return

        if payload is None:
            await self.event.reply(type(self).empty_state_text())
            return

        owner_id = self.event.from_user.id if self.event.from_user else 0
        reply_markup = type(self).build_reply_markup_for_owner(username=username, owner_id=owner_id, payload=payload)
        await type(self).send_response(
            self.event, text=payload.text, image_url=payload.image_url, reply_markup=reply_markup
        )


class BaseLastFMCallbackHandler[C: LastFMCallbackContext, P: LastFMResponsePayload](
    KoroneCallbackQueryHandler, LastFMHandlerSupport
):
    @abstractmethod
    async def resolve_context(self) -> C | None:
        pass

    @classmethod
    @abstractmethod
    async def build_payload_for_username(cls, *, username: str) -> P | None:
        pass

    @classmethod
    async def build_payload(cls, *, context: C) -> P | None:
        return await cls.build_payload_for_username(username=context.username)

    @classmethod
    @abstractmethod
    def empty_state_text(cls) -> str:
        pass

    @classmethod
    def build_reply_markup_for_owner(cls, *, username: str, owner_id: int, payload: P) -> InlineKeyboardMarkup | None:
        return None

    async def handle_not_modified(self) -> None:
        await self.event.answer(_("No updates from your profile."))

    async def render_response(self, message: Message, *, context: C, payload: P) -> None:
        reply_markup = type(self).build_reply_markup_for_owner(
            username=context.username, owner_id=context.owner_id, payload=payload
        )
        await type(self).edit_response(
            message, text=payload.text, image_url=payload.image_url, reply_markup=reply_markup
        )

    @staticmethod
    def _is_message_not_modified(exc: TelegramBadRequest) -> bool:
        return "message is not modified" in exc.message.lower()

    @override
    async def handle(self) -> None:
        await self.check_for_message()

        context = await self.resolve_context()
        if context is None:
            await self.event.answer()
            return

        if not self.can_use_buttons(callback_owner_id=context.owner_id, user_id=self.event.from_user.id):
            await self.event.answer(_("You are not allowed to use this button."), show_alert=True)
            return

        message = cast("Message", self.event.message)
        try:
            payload = await type(self).build_payload(context=context)
            if payload is None:
                await message.edit_text(type(self).empty_state_text())
            else:
                await self.render_response(message, context=context, payload=payload)
            await self.event.answer()
        except LastFMError as exc:
            await self.event.answer(format_lastfm_error(exc), show_alert=True)
        except TelegramBadRequest as exc:
            if self._is_message_not_modified(exc):
                await self.handle_not_modified()
                return
            raise
