import asyncio
import hashlib
from time import perf_counter
from typing import TYPE_CHECKING, ClassVar

import sentry_sdk
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramRetryAfter
from aiogram.utils.chat_action import ChatActionSender

from korone.logger import get_logger
from korone.modules.medias.filters import MediaUrlFilter
from korone.modules.medias.utils.cache import delete_cached_post_and_sources, get_cached_post, set_cached_post
from korone.modules.medias.utils.delivery import MediaDelivery
from korone.modules.medias.utils.platforms import PROVIDERS
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.modules.medias.utils.types import MediaRequest
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.telegram_permissions import handle_no_rights_error, is_no_rights_error

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.modules.medias.utils.types import MediaPost

logger = get_logger(__name__)


def _media_source_id(source_url: str) -> str:
    return hashlib.sha256(source_url.encode()).hexdigest()[:16]


class MediaHandler(KoroneMessageHandler):
    _REQUEST_TIMEOUT_NETWORK_ERROR_TOKENS: ClassVar[tuple[str, ...]] = ("request timeout error",)

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (MediaUrlFilter(PROVIDERS),)

    @classmethod
    def _is_request_timeout_network_error(cls, error: TelegramNetworkError) -> bool:
        normalized_message = str(error).casefold()
        return any(token in normalized_message for token in cls._REQUEST_TIMEOUT_NETWORK_ERROR_TOKENS)

    def _resolve_request(self) -> MediaRequest | None:
        request = self.data.get("media_request")
        if not isinstance(request, MediaRequest):
            return None

        provider = request.provider
        if not isinstance(provider, type) or not issubclass(provider, MediaProvider) or provider not in PROVIDERS:
            return None
        if not isinstance(request.url, str) or not request.url:
            return None
        return request

    async def _fetch_post(self, request: MediaRequest) -> MediaPost | None:
        async with ChatActionSender.typing(
            chat_id=self.event.chat.id, bot=self.bot, message_thread_id=self.event.message_thread_id
        ):
            return await request.provider.safe_fetch(request.url)

    @staticmethod
    async def _try_send_cached_post(request: MediaRequest, delivery: MediaDelivery) -> bool:
        if not (cached_post_payload := await get_cached_post(request.provider, request.url)):
            return False

        cached_url, cached_post = cached_post_payload
        try:
            await delivery.send(cached_post)
        except TelegramBadRequest:
            await delete_cached_post_and_sources(cached_post, request.url, cached_url, cached_post.url)
            return False

        return True

    def _set_handler_context(
        self,
        *,
        request: MediaRequest,
        source_id: str,
        stage: str,
        outcome: str,
        duration_seconds: float,
        stage_durations_seconds: dict[str, float],
    ) -> None:
        sentry_sdk.set_tag("korone.media_stage", stage)
        sentry_sdk.set_tag("korone.media_outcome", outcome)
        sentry_sdk.set_context(
            "media_handler",
            {
                "provider": request.provider.name,
                "handler": self.__class__.__name__,
                "source_id": source_id,
                "stage": stage,
                "outcome": outcome,
                "duration_seconds": round(duration_seconds, 3),
                "stage_durations_seconds": {
                    name: round(duration, 3) for name, duration in stage_durations_seconds.items()
                },
            },
        )

    async def handle(self) -> None:
        if not self.bot or not (request := self._resolve_request()):
            return

        source_identifier = _media_source_id(request.url)
        started_at = perf_counter()
        stage = "resolve"
        stage_started_at = started_at
        outcome = "ignored"
        stage_durations: dict[str, float] = {}
        try:
            await logger.ainfo(
                "[Medias] Handler started",
                provider=request.provider.name,
                handler=self.__class__.__name__,
                source_id=source_identifier,
            )
            delivery = MediaDelivery(self.bot, self.event, request.provider)

            stage = "cache_send"
            stage_started_at = perf_counter()
            if await self._try_send_cached_post(request, delivery):
                stage_durations[stage] = perf_counter() - stage_started_at
                outcome = "cached"
                return
            stage_durations[stage] = perf_counter() - stage_started_at

            stage = "fetch"
            stage_started_at = perf_counter()
            post = await self._fetch_post(request)
            stage_durations[stage] = perf_counter() - stage_started_at
            if not post:
                outcome = "not_found"
                await logger.adebug(
                    "[Medias] Could not fetch post", provider=request.provider.name, source_id=source_identifier
                )
                return

            stage = "send"
            stage_started_at = perf_counter()
            cached_media_payload = await delivery.send(post)
            stage_durations[stage] = perf_counter() - stage_started_at
            if not cached_media_payload:
                outcome = "send_failed"
                await logger.adebug(
                    "[Medias] Could not send media",
                    provider=request.provider.name,
                    source_id=source_identifier,
                    media_count=len(post.media),
                )
                return

            stage = "cache_store"
            stage_started_at = perf_counter()
            await set_cached_post(request.url, post, cached_media_payload)
            stage_durations[stage] = perf_counter() - stage_started_at
            outcome = "sent"
        except asyncio.CancelledError:
            outcome = "cancelled"
            raise
        except Exception as error:  # ruff: ignore[blind-except]
            outcome = "failed"
            if isinstance(error, TelegramNetworkError) and self._is_request_timeout_network_error(error):
                outcome = "send_timeout"
                await logger.awarning(
                    "[Medias] Media send request timed out; delivery status is unknown",
                    provider=request.provider.name,
                    source_id=source_identifier,
                    chat_id=self.event.chat.id,
                    message_id=self.event.message_id,
                    message_thread_id=self.event.message_thread_id,
                    handler=self.__class__.__name__,
                    request_timeout_seconds=MediaDelivery.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
                )
                return

            if isinstance(error, TelegramRetryAfter):
                outcome = "rate_limited"
                await logger.awarning(
                    "[Medias] Media send remained rate limited after retries",
                    provider=request.provider.name,
                    source_id=source_identifier,
                    chat_id=self.event.chat.id,
                    retry_after_seconds=error.retry_after,
                )
                return

            if is_no_rights_error(error) and await handle_no_rights_error(self.bot, self.event.chat, error):
                outcome = "permission_denied"
                return

            await logger.aexception(
                "[Medias] Handler failed",
                provider=request.provider.name,
                source_id=source_identifier,
                chat_id=self.event.chat.id,
                message_id=self.event.message_id,
                message_thread_id=self.event.message_thread_id,
                handler=self.__class__.__name__,
            )
        finally:
            stage_durations.setdefault(stage, perf_counter() - stage_started_at)
            duration_seconds = perf_counter() - started_at
            self._set_handler_context(
                request=request,
                source_id=source_identifier,
                stage=stage,
                outcome=outcome,
                duration_seconds=duration_seconds,
                stage_durations_seconds=stage_durations,
            )
            await logger.ainfo(
                "[Medias] Handler finished",
                provider=request.provider.name,
                handler=self.__class__.__name__,
                source_id=source_identifier,
                stage=stage,
                outcome=outcome,
                duration_seconds=round(duration_seconds, 3),
                stage_durations_seconds={name: round(duration, 3) for name, duration in stage_durations.items()},
            )
