import asyncio
from typing import TYPE_CHECKING, Any, ClassVar, cast

from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.media_group import MediaGroupBuilder

from korone.logger import get_logger
from korone.ui.rendering import caption_kwargs
from korone.utils.telegram_errors import normalized_error_message

from .captions import build_caption, build_keyboard
from .models import DeliveredMedia, DeliveryReceipt, MediaKind, MediaPost, PreparedMedia, ProviderInfo

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from contextlib import AbstractAsyncContextManager

    from aiogram import Bot
    from aiogram.types import InlineKeyboardMarkup, MediaUnion, Message, ReplyParameters

    from korone.ui import MessageContent

    from .transforms import PhotoProcessor

logger = get_logger(__name__)


class TelegramMediaDelivery:
    MEDIA_GROUP_LIMIT: ClassVar[int] = 10
    SEND_REQUEST_TIMEOUT_SECONDS: ClassVar[int] = 180
    SEND_RETRY_ATTEMPTS: ClassVar[int] = 3
    VIDEO_SUPPORTS_STREAMING: ClassVar[bool] = True
    _RETRYABLE_PHOTO_ERROR_TOKENS: ClassVar[tuple[str, ...]] = (
        "too big for a photo",
        "photo invalid dimensions",
        "invalid dimensions",
        "image process failed",
    )

    def __init__(self, message: Message, provider: ProviderInfo, photos: PhotoProcessor) -> None:
        if (bot := message.bot) is None:
            msg = "Media delivery requires a message mounted to a bot"
            raise RuntimeError(msg)
        self._bot: Bot = bot
        self._message = message
        self._provider = provider
        self._photos = photos

    async def send(self, post: MediaPost) -> DeliveryReceipt:
        media_items = post.media[: self.MEDIA_GROUP_LIMIT]
        if not media_items:
            return DeliveryReceipt(())

        if len(media_items) == 1:
            media = await self._photos.prepare(media_items[0])
            caption = build_caption(post, self._provider, include_link=False)
            keyboard = build_keyboard(post)
            return await self._send_single(media, caption, keyboard)

        prepared = await self._photos.prepare_many(media_items, force=False)
        caption = build_caption(post, self._provider, include_link=True)
        async with ChatActionSender.upload_document(**self._chat_action_kwargs()):
            return await self._send_group(prepared, caption)

    def _chat_action_kwargs(self) -> dict[str, Any]:
        return {
            "chat_id": self._message.chat.id,
            "bot": self._bot,
            "message_thread_id": self._message.message_thread_id,
        }

    def _reply_parameters(self) -> ReplyParameters:
        return self._message.as_reply_parameters(allow_sending_without_reply=True)

    def _upload_action(self, kind: MediaKind) -> AbstractAsyncContextManager[Any]:
        kwargs = self._chat_action_kwargs()
        match kind:
            case MediaKind.PHOTO:
                return ChatActionSender.upload_photo(**kwargs)
            case MediaKind.VIDEO:
                return ChatActionSender.upload_video(**kwargs)
        msg = f"Unsupported media kind: {kind!r}"
        raise ValueError(msg)

    async def _send_single(
        self, media: PreparedMedia, caption: MessageContent, keyboard: InlineKeyboardMarkup | None
    ) -> DeliveryReceipt:
        async with self._upload_action(media.kind):
            sent = await self._send_media(media, caption, keyboard)
        return self._build_receipt(((media, sent),))

    async def _send_media(
        self, media: PreparedMedia, caption: MessageContent, keyboard: InlineKeyboardMarkup | None
    ) -> Message:
        async def send() -> Message:
            match media.kind:
                case MediaKind.PHOTO:
                    return await self._send_photo_with_fallback(media, caption, keyboard)
                case MediaKind.VIDEO:
                    return await self._send_video(media, caption, keyboard)
            msg = f"Unsupported media kind: {media.kind!r}"
            raise ValueError(msg)

        return await self._retry_flood_control(send)

    async def _send_photo_with_fallback(
        self, media: PreparedMedia, caption: MessageContent, keyboard: InlineKeyboardMarkup | None
    ) -> Message:
        try:
            return await self._send_photo(media, caption, keyboard)
        except TelegramBadRequest as error:
            if not self._is_retryable_photo_error(error):
                raise
            original_error = error

        compressed = await self._photos.prepare(media, force=True)
        if compressed is media:
            raise original_error
        return await self._send_photo(compressed, caption, keyboard)

    async def _send_photo(
        self, media: PreparedMedia, caption: MessageContent, keyboard: InlineKeyboardMarkup | None
    ) -> Message:
        method = self._message.answer_photo(
            photo=media.file,
            **caption_kwargs(caption),
            reply_parameters=self._reply_parameters(),
            reply_markup=keyboard,
        )
        return await self._bot(method, request_timeout=self.SEND_REQUEST_TIMEOUT_SECONDS)

    async def _send_video(
        self, media: PreparedMedia, caption: MessageContent, keyboard: InlineKeyboardMarkup | None
    ) -> Message:
        method = self._message.answer_video(
            video=media.file,
            **caption_kwargs(caption),
            reply_parameters=self._reply_parameters(),
            reply_markup=keyboard,
            duration=media.duration,
            width=media.width,
            height=media.height,
            thumbnail=media.thumbnail,
            supports_streaming=self.VIDEO_SUPPORTS_STREAMING,
        )
        return await self._bot(method, request_timeout=self.SEND_REQUEST_TIMEOUT_SECONDS)

    async def _send_group(self, media_items: tuple[PreparedMedia, ...], caption: MessageContent) -> DeliveryReceipt:
        try:
            sent_messages = await self._send_group_messages(self._build_group(media_items, caption))
        except TelegramBadRequest as error:
            if not self._is_retryable_photo_error(error):
                raise
            forced = await self._photos.prepare_many(media_items, force=True)
            if forced == media_items:
                raise
            media_items = forced
            sent_messages = await self._send_group_messages(self._build_group(media_items, caption))
        return self._build_receipt(tuple(zip(media_items, sent_messages, strict=False)))

    async def _send_group_messages(self, media_group: list[MediaUnion]) -> list[Message]:
        method = self._message.answer_media_group(media=media_group, reply_parameters=self._reply_parameters())
        return await self._retry_flood_control(
            lambda: self._bot(method, request_timeout=self.SEND_REQUEST_TIMEOUT_SECONDS)
        )

    @classmethod
    def _build_group(cls, media_items: tuple[PreparedMedia, ...], caption: MessageContent) -> list[MediaUnion]:
        builder = MediaGroupBuilder()
        last_index = len(media_items) - 1
        for index, item in enumerate(media_items):
            payload = caption_kwargs(caption) if index == last_index else {}
            match item.kind:
                case MediaKind.PHOTO:
                    builder.add_photo(item.file, **payload)
                case MediaKind.VIDEO:
                    builder.add_video(
                        item.file,
                        **payload,
                        duration=item.duration,
                        width=item.width,
                        height=item.height,
                        thumbnail=item.thumbnail,
                        supports_streaming=cls.VIDEO_SUPPORTS_STREAMING,
                    )
        return cast("list[MediaUnion]", builder.build())

    async def _retry_flood_control[Result](self, operation: Callable[[], Awaitable[Result]]) -> Result:
        for attempt in range(1, self.SEND_RETRY_ATTEMPTS + 1):
            try:
                return await operation()
            except TelegramRetryAfter as error:
                if attempt == self.SEND_RETRY_ATTEMPTS:
                    raise
                await logger.awarning(
                    "[Medias] Telegram flood control requested a retry",
                    chat_id=self._message.chat.id,
                    attempt=attempt,
                    retry_after_seconds=error.retry_after,
                )
                await asyncio.sleep(error.retry_after)
        msg = "Media send retry loop exhausted without returning or raising"
        raise RuntimeError(msg)

    @classmethod
    def _build_receipt(cls, sent_media: tuple[tuple[PreparedMedia, Message], ...]) -> DeliveryReceipt:
        delivered: list[DeliveredMedia] = []
        for media, sent_message in sent_media:
            file_id = cls._extract_file_id(sent_message, media.kind)
            if file_id:
                delivered.append(DeliveredMedia(media=media, file_id=file_id))
        return DeliveryReceipt(tuple(delivered))

    @staticmethod
    def _extract_file_id(sent_message: Message, kind: MediaKind) -> str | None:
        match kind:
            case MediaKind.PHOTO if sent_message.photo:
                return sent_message.photo[-1].file_id
            case MediaKind.VIDEO if sent_message.video:
                return sent_message.video.file_id
        return None

    @classmethod
    def _is_retryable_photo_error(cls, error: TelegramBadRequest) -> bool:
        message = normalized_error_message(error)
        return any(token in message for token in cls._RETRYABLE_PHOTO_ERROR_TOKENS)
