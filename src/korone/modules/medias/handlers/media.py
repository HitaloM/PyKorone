import asyncio
import hashlib
from dataclasses import dataclass, field
from time import perf_counter
from typing import TYPE_CHECKING, ClassVar

import sentry_sdk
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.utils.chat_action import ChatActionSender

from korone.logger import get_logger
from korone.modules.medias.container import media_container
from korone.modules.medias.delivery import TelegramMediaDelivery
from korone.modules.medias.filters import MediaUrlFilter
from korone.modules.medias.models import MediaOutcome, MediaRequest, MediaStage
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.telegram_errors import normalized_error_message
from korone.utils.telegram_permissions import handle_no_rights_error, is_no_rights_error

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

logger = get_logger(__name__)


def _source_id(source_url: str) -> str:
    return hashlib.sha256(source_url.encode()).hexdigest()[:16]


@dataclass(slots=True)
class _MediaRun:
    request: MediaRequest
    source_id: str
    handler_name: str
    started_at: float = field(default_factory=perf_counter)
    stage: MediaStage = MediaStage.RESOLVE
    outcome: MediaOutcome = MediaOutcome.IGNORED
    stage_durations: dict[MediaStage, float] = field(default_factory=dict)
    stage_started_at: float = field(init=False)

    def __post_init__(self) -> None:
        self.stage_started_at = self.started_at

    def advance(self, stage: MediaStage) -> None:
        now = perf_counter()
        self.stage_durations[self.stage] = now - self.stage_started_at
        self.stage = stage
        self.stage_started_at = now

    def finish(self) -> float:
        finished_at = perf_counter()
        self.stage_durations.setdefault(self.stage, finished_at - self.stage_started_at)
        duration = finished_at - self.started_at
        sentry_sdk.set_tag("korone.media_stage", self.stage.value)
        sentry_sdk.set_tag("korone.media_outcome", self.outcome.value)
        sentry_sdk.set_context(
            "media_handler",
            {
                "provider": self.request.provider.info.name,
                "handler": self.handler_name,
                "source_id": self.source_id,
                "stage": self.stage.value,
                "outcome": self.outcome.value,
                "duration_seconds": round(duration, 3),
                "stage_durations_seconds": {
                    stage.value: round(elapsed, 3) for stage, elapsed in self.stage_durations.items()
                },
            },
        )
        return duration


class MediaHandler(KoroneMessageHandler):
    _REQUEST_TIMEOUT_TOKENS: ClassVar[tuple[str, ...]] = ("request timeout error",)

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (~Command("url"), MediaUrlFilter(media_container.registry))

    def _resolve_request(self) -> MediaRequest | None:
        request = self.data.get("media_request")
        if not isinstance(request, MediaRequest):
            return None
        if not request.url or not media_container.registry.contains(request.provider):
            return None
        return request

    async def _recover_error(self, error: Exception, run: _MediaRun) -> MediaOutcome:
        provider = run.request.provider.info
        if isinstance(error, TelegramNetworkError) and self._is_request_timeout(error):
            await logger.awarning(
                "[Medias] Media send request timed out; delivery status is unknown",
                provider=provider.name,
                source_id=run.source_id,
                chat_id=self.event.chat.id,
                message_id=self.event.message_id,
                message_thread_id=self.event.message_thread_id,
                handler=self.__class__.__name__,
                request_timeout_seconds=TelegramMediaDelivery.SEND_REQUEST_TIMEOUT_SECONDS,
            )
            return MediaOutcome.SEND_TIMEOUT

        if isinstance(error, TelegramRetryAfter):
            await logger.awarning(
                "[Medias] Media send remained rate limited after retries",
                provider=provider.name,
                source_id=run.source_id,
                chat_id=self.event.chat.id,
                retry_after_seconds=error.retry_after,
            )
            return MediaOutcome.RATE_LIMITED

        if is_no_rights_error(error) and await handle_no_rights_error(self.bot, self.event.chat, error):
            return MediaOutcome.PERMISSION_DENIED

        await logger.aexception(
            "[Medias] Handler failed",
            provider=provider.name,
            source_id=run.source_id,
            chat_id=self.event.chat.id,
            message_id=self.event.message_id,
            message_thread_id=self.event.message_thread_id,
            handler=self.__class__.__name__,
        )
        return MediaOutcome.FAILED

    async def handle(self) -> None:
        if not self.bot or not (request := self._resolve_request()):
            return

        run = _MediaRun(request=request, source_id=_source_id(request.url), handler_name=self.__class__.__name__)
        try:
            await logger.ainfo(
                "[Medias] Handler started",
                provider=request.provider.info.name,
                handler=self.__class__.__name__,
                source_id=run.source_id,
            )
            delivery = media_container.delivery_for(self.event, request.provider)
            run.outcome = await media_container.service.process(
                request,
                delivery,
                on_stage=run.advance,
                fetch_context=ChatActionSender.typing(
                    chat_id=self.event.chat.id, bot=self.bot, message_thread_id=self.event.message_thread_id
                ),
            )
            if run.outcome == MediaOutcome.NOT_FOUND:
                await logger.adebug(
                    "[Medias] Could not fetch post", provider=request.provider.info.name, source_id=run.source_id
                )
        except asyncio.CancelledError:
            run.outcome = MediaOutcome.CANCELLED
            raise
        except Exception as error:  # ruff: ignore[blind-except]
            run.outcome = await self._recover_error(error, run)
        finally:
            duration = run.finish()
            await logger.ainfo(
                "[Medias] Handler finished",
                provider=request.provider.info.name,
                handler=self.__class__.__name__,
                source_id=run.source_id,
                stage=run.stage.value,
                outcome=run.outcome.value,
                duration_seconds=round(duration, 3),
                stage_durations_seconds={
                    stage.value: round(elapsed, 3) for stage, elapsed in run.stage_durations.items()
                },
            )

    @classmethod
    def _is_request_timeout(cls, error: TelegramNetworkError) -> bool:
        message = normalized_error_message(error)
        return any(token in message for token in cls._REQUEST_TIMEOUT_TOKENS)
