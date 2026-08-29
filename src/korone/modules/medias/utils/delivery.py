import asyncio
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import BufferedInputFile
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.media_group import MediaGroupBuilder

from korone.constants import (
    TELEGRAM_PHOTO_MAX_ASPECT_RATIO,
    TELEGRAM_PHOTO_MAX_DIMENSIONS_SUM,
    TELEGRAM_PHOTO_MAX_FILE_SIZE_BYTES,
)
from korone.logger import get_logger
from korone.modules.utils_.telegram_exceptions import REPLIED_NOT_FOUND
from korone.ui.rendering import caption_kwargs

from .cache import MediaCacheEntryPayload, cache_media_file_ids, serialize_media_entry
from .captions import build_caption, build_keyboard
from .photo_compression import compress_photo_payload_to_safe_jpeg, photo_payload_needs_resize
from .resources import MEDIA_TRANSFORM_SLOTS
from .types import MediaItem, MediaKind, MediaPost

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from contextlib import AbstractAsyncContextManager

    from aiogram import Bot
    from aiogram.types import InlineKeyboardMarkup, Message

    from korone.ui import MessageContent

    from .provider_base import MediaProvider

logger = get_logger(__name__)


class MediaDelivery:
    MEDIA_GROUP_LIMIT: ClassVar[int] = 10
    PHOTO_SAFE_LIMIT_BYTES: ClassVar[int] = TELEGRAM_PHOTO_MAX_FILE_SIZE_BYTES - 32 * 1024
    PHOTO_MAX_DIMENSIONS_SUM: ClassVar[int] = TELEGRAM_PHOTO_MAX_DIMENSIONS_SUM
    PHOTO_MAX_ASPECT_RATIO: ClassVar[int] = TELEGRAM_PHOTO_MAX_ASPECT_RATIO
    PHOTO_COMPRESSION_TIMEOUT_SECONDS: ClassVar[float] = 12.0
    MEDIA_SEND_REQUEST_TIMEOUT_SECONDS: ClassVar[int] = 180
    MEDIA_SEND_RETRY_ATTEMPTS: ClassVar[int] = 3
    VIDEO_SUPPORTS_STREAMING: ClassVar[bool] = True
    _MISSING_REPLY_ERROR_TOKENS: ClassVar[tuple[str, ...]] = (REPLIED_NOT_FOUND, "replied message not found")
    _RETRYABLE_PHOTO_ERROR_TOKENS: ClassVar[tuple[str, ...]] = (
        "too big for a photo",
        "photo_invalid_dimensions",
        "invalid dimensions",
        "image_process_failed",
    )

    def __init__(self, bot: Bot, message: Message, provider: type[MediaProvider]) -> None:
        self._bot = bot
        self._message = message
        self._provider = provider

    @classmethod
    def _message_contains_any(cls, error: TelegramBadRequest, tokens: tuple[str, ...]) -> bool:
        message = error.message.casefold()
        return any(token in message for token in tokens)

    @classmethod
    def _is_missing_reply_error(cls, error: TelegramBadRequest) -> bool:
        return cls._message_contains_any(error, cls._MISSING_REPLY_ERROR_TOKENS)

    @classmethod
    def _is_retryable_photo_send_error(cls, error: TelegramBadRequest) -> bool:
        return cls._message_contains_any(error, cls._RETRYABLE_PHOTO_ERROR_TOKENS)

    @staticmethod
    def _extract_sent_file_id(sent_message: Message, kind: MediaKind) -> str | None:
        match kind:
            case MediaKind.PHOTO if sent_message.photo:
                return sent_message.photo[-1].file_id
            case MediaKind.VIDEO if sent_message.video:
                return sent_message.video.file_id
            case _:
                return None

    def _chat_action_kwargs(self) -> dict[str, Any]:
        return {
            "chat_id": self._message.chat.id,
            "bot": self._bot,
            "message_thread_id": self._message.message_thread_id,
        }

    def _upload_action(self, kind: MediaKind) -> AbstractAsyncContextManager[Any]:
        kwargs = self._chat_action_kwargs()
        match kind:
            case MediaKind.PHOTO:
                return ChatActionSender.upload_photo(**kwargs)
            case MediaKind.VIDEO:
                return ChatActionSender.upload_video(**kwargs)
            case _:
                msg = f"Unsupported media kind: {kind!r}"
                raise ValueError(msg)

    @classmethod
    def _compressed_photo_filename(cls, original_name: str) -> str:
        stem = Path(original_name).stem or "photo"
        return f"{stem}_compressed.jpg"

    @classmethod
    def _prepare_photo_payload(cls, payload: bytes, *, force: bool) -> bytes | None:
        if not force and len(payload) <= cls.PHOTO_SAFE_LIMIT_BYTES:
            needs_resize = photo_payload_needs_resize(
                payload, max_dimensions_sum=cls.PHOTO_MAX_DIMENSIONS_SUM, max_aspect_ratio=cls.PHOTO_MAX_ASPECT_RATIO
            )
            if not needs_resize:
                return None

        return compress_photo_payload_to_safe_jpeg(
            payload,
            safe_limit_bytes=cls.PHOTO_SAFE_LIMIT_BYTES,
            max_dimensions_sum=cls.PHOTO_MAX_DIMENSIONS_SUM,
            max_aspect_ratio=cls.PHOTO_MAX_ASPECT_RATIO,
        )

    async def _compress_photo(self, media: MediaItem, *, force: bool = False) -> MediaItem:
        if media.kind != MediaKind.PHOTO or not isinstance(media.file, BufferedInputFile):
            return media

        async with MEDIA_TRANSFORM_SLOTS:
            try:
                async with asyncio.timeout(self.PHOTO_COMPRESSION_TIMEOUT_SECONDS):
                    compressed_payload = await asyncio.to_thread(
                        self._prepare_photo_payload, media.file.data, force=force
                    )
            except TimeoutError:
                await logger.adebug(
                    "[Medias] Photo compression timed out",
                    source_url=media.source_url,
                    timeout_seconds=self.PHOTO_COMPRESSION_TIMEOUT_SECONDS,
                )
                return media
            except Exception:  # ruff: ignore[blind-except]
                return media

        if not compressed_payload:
            return media

        filename = self._compressed_photo_filename(media.filename)
        return replace(media, file=BufferedInputFile(compressed_payload, filename), filename=filename)

    async def _prepare_photos_for_send(self, media_items: list[MediaItem], *, force: bool) -> list[MediaItem]:
        indexes_to_process = [
            index
            for index, item in enumerate(media_items)
            if item.kind == MediaKind.PHOTO and isinstance(item.file, BufferedInputFile)
        ]
        if not indexes_to_process:
            return media_items

        prepared = media_items.copy()
        tasks: dict[int, asyncio.Task[MediaItem]] = {}
        async with asyncio.TaskGroup() as tg:
            for index in indexes_to_process:
                tasks[index] = tg.create_task(self._compress_photo(media_items[index], force=force))

        for index, task in tasks.items():
            prepared[index] = task.result()
        return prepared

    async def _send_photo(
        self, media: MediaItem, caption: MessageContent, keyboard: InlineKeyboardMarkup | None, *, reply: bool
    ) -> Message:
        if reply:
            return await self._message.reply_photo(
                media.file,
                **caption_kwargs(caption),
                reply_markup=keyboard,
                request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
            )

        return await self._bot.send_photo(
            chat_id=self._message.chat.id,
            photo=media.file,
            **caption_kwargs(caption),
            reply_markup=keyboard,
            message_thread_id=self._message.message_thread_id,
            request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
        )

    async def _send_photo_with_resize_fallback(
        self, media: MediaItem, caption: MessageContent, keyboard: InlineKeyboardMarkup | None, *, reply: bool
    ) -> Message:
        try:
            return await self._send_photo(media, caption, keyboard, reply=reply)
        except TelegramBadRequest as error:
            if not self._is_retryable_photo_send_error(error):
                raise
            oversized_error = error

        compressed = await self._compress_photo(media, force=True)
        if compressed is media:
            raise oversized_error

        return await self._send_photo(compressed, caption, keyboard, reply=reply)

    async def _send_video(
        self, media: MediaItem, caption: MessageContent, keyboard: InlineKeyboardMarkup | None, *, reply: bool
    ) -> Message:
        if reply:
            return await self._message.reply_video(
                media.file,
                **caption_kwargs(caption),
                reply_markup=keyboard,
                duration=media.duration,
                width=media.width,
                height=media.height,
                thumbnail=media.thumbnail,
                supports_streaming=self.VIDEO_SUPPORTS_STREAMING,
                request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
            )

        return await self._bot.send_video(
            chat_id=self._message.chat.id,
            video=media.file,
            **caption_kwargs(caption),
            reply_markup=keyboard,
            duration=media.duration,
            width=media.width,
            height=media.height,
            thumbnail=media.thumbnail,
            supports_streaming=self.VIDEO_SUPPORTS_STREAMING,
            message_thread_id=self._message.message_thread_id,
            request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
        )

    async def _send_media(
        self, media: MediaItem, caption: MessageContent, keyboard: InlineKeyboardMarkup | None, *, reply: bool
    ) -> Message:
        async def send() -> Message:
            match media.kind:
                case MediaKind.PHOTO:
                    return await self._send_photo_with_resize_fallback(media, caption, keyboard, reply=reply)
                case MediaKind.VIDEO:
                    return await self._send_video(media, caption, keyboard, reply=reply)
                case _:
                    msg = f"Unsupported media kind: {media.kind!r}"
                    raise ValueError(msg)

        return await self._retry_after_flood_control(send)

    async def _retry_after_flood_control[Result](self, operation: Callable[[], Awaitable[Result]]) -> Result:
        for attempt in range(1, self.MEDIA_SEND_RETRY_ATTEMPTS + 1):
            try:
                return await operation()
            except TelegramRetryAfter as error:
                if attempt == self.MEDIA_SEND_RETRY_ATTEMPTS:
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

    async def _cache_sent_media(self, sent_media: list[tuple[MediaItem, Message]]) -> list[MediaCacheEntryPayload]:
        serialized_media: list[MediaCacheEntryPayload] = []
        cache_entries: list[tuple[str, str]] = []
        for media, sent_message in sent_media:
            if not (file_id := self._extract_sent_file_id(sent_message, media.kind)):
                continue
            serialized_media.append(serialize_media_entry(media, file_id))
            if not isinstance(media.file, str):
                cache_entries.append((media.source_url, file_id))

        await cache_media_file_ids(cache_entries)
        return serialized_media

    async def _send_single_media(
        self, media: MediaItem, caption: MessageContent, keyboard: InlineKeyboardMarkup | None
    ) -> list[MediaCacheEntryPayload]:
        media = await self._compress_photo(media, force=False)
        async with self._upload_action(media.kind):
            try:
                sent_message = await self._send_media(media, caption, keyboard, reply=True)
            except TelegramBadRequest as error:
                if not self._is_missing_reply_error(error):
                    raise
                sent_message = await self._send_media(media, caption, keyboard, reply=False)

        return await self._cache_sent_media([(media, sent_message)])

    @classmethod
    def _add_group_item(cls, builder: MediaGroupBuilder, item: MediaItem, caption: MessageContent | None) -> None:
        payload = caption_kwargs(caption) if caption is not None else {}
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
            case _:
                msg = f"Unsupported media kind: {item.kind!r}"
                raise ValueError(msg)

    async def _send_media_group_messages(self, media_group: list[Any]) -> list[Message]:
        async def send(reply_to_message_id: int | None) -> list[Message]:
            return await self._retry_after_flood_control(
                lambda: self._bot.send_media_group(
                    chat_id=self._message.chat.id,
                    media=media_group,
                    reply_to_message_id=reply_to_message_id,
                    message_thread_id=self._message.message_thread_id,
                    request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
                )
            )

        try:
            return await send(self._message.message_id)
        except TelegramBadRequest as error:
            if not self._is_missing_reply_error(error):
                raise
            return await send(None)

    @classmethod
    def _build_media_group(cls, media_items: list[MediaItem], caption: MessageContent) -> list[Any]:
        builder = MediaGroupBuilder()
        last_index = len(media_items) - 1
        for index, item in enumerate(media_items):
            cls._add_group_item(builder, item, caption if index == last_index else None)

        return builder.build()

    async def _send_media_group(
        self, media_items: list[MediaItem], caption: MessageContent
    ) -> list[MediaCacheEntryPayload]:
        try:
            media_group = self._build_media_group(media_items, caption)
            sent_messages = await self._send_media_group_messages(media_group)
        except TelegramBadRequest as error:
            if not self._is_retryable_photo_send_error(error):
                raise

            forced_media_items = await self._prepare_photos_for_send(media_items, force=True)
            if forced_media_items == media_items:
                raise

            media_group = self._build_media_group(forced_media_items, caption)
            sent_messages = await self._send_media_group_messages(media_group)
            media_items = forced_media_items

        return await self._cache_sent_media(list(zip(media_items, sent_messages, strict=False)))

    async def send(self, post: MediaPost) -> list[MediaCacheEntryPayload]:
        media_items = post.media[: self.MEDIA_GROUP_LIMIT]
        if not media_items:
            return []

        media_items = await self._prepare_photos_for_send(media_items, force=False)
        if len(media_items) == 1:
            caption = build_caption(post, self._provider, include_link=False)
            keyboard = build_keyboard(post)
            cached_media_payload = await self._send_single_media(media_items[0], caption, keyboard)
            if len(cached_media_payload) != 1:
                return []
            return cached_media_payload

        group_caption = build_caption(post, self._provider, include_link=True)
        async with ChatActionSender.upload_document(**self._chat_action_kwargs()):
            cached_media_payload = await self._send_media_group(media_items, group_caption)

        if len(cached_media_payload) != len(media_items):
            return []
        return cached_media_payload
