import asyncio
from typing import TYPE_CHECKING, Protocol

from aiogram.exceptions import TelegramBadRequest

from korone.logger import get_logger

from .models import DeliveryReceipt, MediaOutcome, MediaPost, MediaRequest, MediaStage

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractAsyncContextManager

    from .cache import MediaCache

logger = get_logger(__name__)


class MediaDelivery(Protocol):
    async def send(self, post: MediaPost) -> DeliveryReceipt: ...


class MediaService:
    __slots__ = ("_cache",)

    def __init__(self, cache: MediaCache) -> None:
        self._cache = cache

    async def process(
        self,
        request: MediaRequest,
        delivery: MediaDelivery,
        *,
        on_stage: Callable[[MediaStage], None],
        fetch_context: AbstractAsyncContextManager[object],
    ) -> MediaOutcome:
        on_stage(MediaStage.CACHE_SEND)
        cached_payload = await self._cache.get_post(request.provider.info, request.url)
        if cached_payload is not None:
            cached_url, cached_post = cached_payload
            try:
                await delivery.send(cached_post)
            except TelegramBadRequest:
                await self._cache.delete_post_and_sources(cached_post, request.url, cached_url, cached_post.url)
            else:
                return MediaOutcome.CACHED

        on_stage(MediaStage.FETCH)
        async with fetch_context:
            post = await self._safe_fetch(request)
        if post is None:
            return MediaOutcome.NOT_FOUND

        on_stage(MediaStage.SEND)
        receipt = await delivery.send(post)
        expected_count = min(len(post.media), 10)
        if len(receipt.media) != expected_count:
            await logger.adebug(
                "[Medias] Could not collect sent media",
                provider=request.provider.info.name,
                media_count=len(post.media),
                receipt_count=len(receipt.media),
            )
            return MediaOutcome.SEND_FAILED

        on_stage(MediaStage.CACHE_STORE)
        await self._cache.set_source_file_ids(
            tuple(
                (delivered.media.source_url, delivered.file_id)
                for delivered in receipt.media
                if not isinstance(delivered.media.file, str)
            )
        )
        await self._cache.set_post(request.url, post, receipt)
        return MediaOutcome.SENT

    @staticmethod
    async def _safe_fetch(request: MediaRequest) -> MediaPost | None:
        try:
            return await request.provider.fetch(request.url)
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            await logger.awarning(
                "[Medias] Provider fetch timed out", provider=request.provider.info.name, source_url=request.url
            )
            return None
        except Exception:  # ruff: ignore[blind-except]
            await logger.aexception(
                "[Medias] Provider fetch failed", provider=request.provider.info.name, source_url=request.url
            )
            return None
