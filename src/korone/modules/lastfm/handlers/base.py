from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, override

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputMediaPhoto

from korone.db.repositories.lastfm import LastFMRepository
from korone.logger import get_logger
from korone.modules.lastfm.utils import LastFMError, format_lastfm_error
from korone.modules.utils_.reply_or_edit import edit_message_text, reply_message
from korone.ui.rendering import caption_kwargs
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.telegram_errors import (
    is_bad_media_url_error,
    is_callback_query_expired_error,
    is_message_not_modified_error,
)

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup, Message

    from korone.ui import MessageContent

LASTFM_FALLBACK_IMAGE_URL = "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png"

logger = get_logger(__name__)


class LastFMResponsePayload(Protocol):
    @property
    def text(self) -> MessageContent: ...

    @property
    def image_url(self) -> str | None: ...


@dataclass(slots=True, frozen=True)
class LastFMUserContext:
    username: str
    display_name: str
    telegram_user_id: int


class LastFMHandlerSupport:
    @classmethod
    async def reply_missing_username(cls, message: Message) -> None:
        await reply_message(message, cls.missing_username_text())

    @staticmethod
    def can_use_buttons(*, callback_owner_id: int, user_id: int) -> bool:
        return callback_owner_id in {0, user_id}

    @staticmethod
    async def resolve_username_for_user(user_id: int | None) -> str | None:
        if not user_id:
            return None

        return await LastFMRepository.get_username(user_id)

    @classmethod
    async def resolve_user_context_from_message(cls, message: Message) -> LastFMUserContext | None:
        if not message.from_user:
            return None

        username = await cls.resolve_username_for_user(message.from_user.id)
        if not username:
            return None

        return LastFMUserContext(
            username=username, display_name=message.from_user.first_name, telegram_user_id=message.from_user.id
        )

    @staticmethod
    def missing_username_text() -> str:
        return _("You need to set your Last.fm username first. Use /setlfm username.")

    @staticmethod
    def resolve_image_url(image_url: str | None) -> str:
        return image_url or LASTFM_FALLBACK_IMAGE_URL

    @classmethod
    def _resolve_image_url_candidates(cls, image_url: str | None) -> tuple[str, ...]:
        primary_url = cls.resolve_image_url(image_url)
        if primary_url == LASTFM_FALLBACK_IMAGE_URL:
            return (LASTFM_FALLBACK_IMAGE_URL,)

        return (primary_url, LASTFM_FALLBACK_IMAGE_URL)

    @classmethod
    async def send_response(
        cls,
        message: Message,
        *,
        text: MessageContent,
        image_url: str | None,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> Message:
        for candidate_url in cls._resolve_image_url_candidates(image_url):
            try:
                return await message.reply_photo(photo=candidate_url, **caption_kwargs(text, reply_markup=reply_markup))
            except TelegramBadRequest as exc:
                if not is_bad_media_url_error(exc):
                    raise
                await logger.awarning(
                    "[LastFM] Telegram rejected album art URL while sending response",
                    image_url=candidate_url,
                    chat_id=message.chat.id,
                    source_message_id=message.message_id,
                    error=exc.message,
                )

        return await reply_message(message, text, reply_markup=reply_markup)

    @classmethod
    async def edit_response(
        cls,
        message: Message,
        *,
        text: MessageContent,
        image_url: str | None,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        if not message.photo:
            await edit_message_text(message, text, reply_markup=reply_markup)
            return

        for candidate_url in cls._resolve_image_url_candidates(image_url):
            try:
                await message.edit_media(
                    media=InputMediaPhoto(media=candidate_url, **caption_kwargs(text)), reply_markup=reply_markup
                )
            except TelegramBadRequest as exc:
                if not is_bad_media_url_error(exc):
                    raise
                await logger.awarning(
                    "[LastFM] Telegram rejected album art URL while editing response",
                    image_url=candidate_url,
                    chat_id=message.chat.id,
                    target_message_id=message.message_id,
                    error=exc.message,
                )
            else:
                return

        await message.edit_caption(**caption_kwargs(text, reply_markup=reply_markup))


class BaseLastFMMessageHandler[P: LastFMResponsePayload](KoroneMessageHandler, LastFMHandlerSupport):
    @classmethod
    @abstractmethod
    async def build_payload_for_user(cls, *, user: LastFMUserContext) -> P | None:
        pass

    @classmethod
    @abstractmethod
    def empty_state_text(cls) -> str:
        pass

    @classmethod
    def build_reply_markup_for_user(cls, *, user: LastFMUserContext, payload: P) -> InlineKeyboardMarkup | None:
        return None

    @override
    async def handle(self) -> None:
        user = await type(self).resolve_user_context_from_message(self.event)
        if not user:
            await type(self).reply_missing_username(self.event)
            return

        try:
            payload = await type(self).build_payload_for_user(user=user)
        except LastFMError as exc:
            await self.answer(format_lastfm_error(exc))
            return

        if payload is None:
            await self.answer(type(self).empty_state_text())
            return

        reply_markup = type(self).build_reply_markup_for_user(user=user, payload=payload)
        await type(self).send_response(
            self.event, text=payload.text, image_url=payload.image_url, reply_markup=reply_markup
        )


class BaseLastFMCallbackHandler[C: LastFMUserContext, P: LastFMResponsePayload](
    KoroneCallbackQueryHandler, LastFMHandlerSupport
):
    @abstractmethod
    async def resolve_context(self) -> C | None:
        pass

    @classmethod
    @abstractmethod
    async def build_payload_for_user(cls, *, user: LastFMUserContext) -> P | None:
        pass

    @classmethod
    async def build_payload(cls, *, context: C) -> P | None:
        return await cls.build_payload_for_user(user=context)

    @classmethod
    @abstractmethod
    def empty_state_text(cls) -> str:
        pass

    @classmethod
    def build_reply_markup_for_user(cls, *, user: LastFMUserContext, payload: P) -> InlineKeyboardMarkup | None:
        return None

    async def handle_not_modified(self) -> None:
        await self._answer_callback_safely(_("No updates from your profile."))

    async def render_response(self, message: Message, *, context: C, payload: P) -> None:
        reply_markup = type(self).build_reply_markup_for_user(user=context, payload=payload)
        await type(self).edit_response(
            message, text=payload.text, image_url=payload.image_url, reply_markup=reply_markup
        )

    async def _answer_callback_safely(self, text: str | None = None, *, show_alert: bool = False) -> None:
        try:
            await self.event.answer(text=text, show_alert=show_alert)
        except TelegramBadRequest as exc:
            if not is_callback_query_expired_error(exc):
                raise
            await logger.adebug(
                "LastFM callback query expired while answering", callback_query_id=self.event.id, error=exc.message
            )

    @override
    async def handle(self) -> None:
        await self.check_for_message()

        context = await self.resolve_context()
        if context is None:
            await self._answer_callback_safely()
            return

        if not self.can_use_buttons(callback_owner_id=context.telegram_user_id, user_id=self.event.from_user.id):
            await self._answer_callback_safely(_("You are not allowed to use this button."), show_alert=True)
            return

        message = self.message
        await self._answer_callback_safely()
        try:
            payload = await type(self).build_payload(context=context)
            if payload is None:
                await edit_message_text(message, type(self).empty_state_text())
            else:
                await self.render_response(message, context=context, payload=payload)
        except LastFMError as exc:
            await self._answer_callback_safely(format_lastfm_error(exc), show_alert=True)
        except TelegramBadRequest as exc:
            if is_message_not_modified_error(exc):
                await self.handle_not_modified()
                return
            raise
