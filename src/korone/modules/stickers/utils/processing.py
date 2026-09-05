import asyncio
import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter
from typing import Any, Final

import sentry_sdk
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message, TelegramObject

from korone.logger import get_logger
from korone.modules.utils_.reply_or_edit import reply_message

logger = get_logger(__name__)

_JOB_KEY_PREFIX: Final = "korone:sticker-pack-processing"
_MAX_CONCURRENT_JOBS: Final = 2
_MAX_PENDING_JOBS: Final = 32
_MAX_JOB_SECONDS: Final = 30 * 60
_SHUTDOWN_TIMEOUT_SECONDS: Final = 30

type StickerPackHandler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class StickerPackSubmission(StrEnum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    BUSY = "busy"


def sticker_pack_job_key(user_id: int, pack_title: str) -> str:
    digest = hashlib.sha256(f"{user_id}:{pack_title.lower()}".encode()).hexdigest()
    return f"{_JOB_KEY_PREFIX}:{digest}"


@dataclass(frozen=True, slots=True)
class StickerPackJob:
    handler: StickerPackHandler
    event: Message
    data: dict[str, Any]
    job_key: str
    job_id: str
    queued_at: float
    failure_text: str


class StickerPackProcessingManager:
    def __init__(self) -> None:
        self._accepting = False
        self._tasks: set[asyncio.Task[None]] = set()
        self._active_job_keys: set[str] = set()
        self._concurrency = asyncio.Semaphore(_MAX_CONCURRENT_JOBS)

    async def start(self) -> None:
        self._accepting = True
        await logger.ainfo(
            "[Stickers] Pack processing manager started",
            max_concurrent_jobs=_MAX_CONCURRENT_JOBS,
            max_pending_jobs=_MAX_PENDING_JOBS,
        )

    async def submit(self, job: StickerPackJob) -> StickerPackSubmission:
        if job.job_key in self._active_job_keys:
            await logger.ainfo("[Stickers] Duplicate pack processing rejected", job_id=job.job_id)
            return StickerPackSubmission.DUPLICATE

        if not self._accepting or len(self._tasks) >= _MAX_PENDING_JOBS:
            await logger.awarning(
                "[Stickers] Pack processing rejected",
                job_id=job.job_id,
                accepting=self._accepting,
                pending_jobs=len(self._tasks),
            )
            return StickerPackSubmission.BUSY

        self._active_job_keys.add(job.job_key)
        task = asyncio.create_task(self._run_tracked(job), name=f"sticker-pack:{job.job_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return StickerPackSubmission.ACCEPTED

    async def _run_tracked(self, job: StickerPackJob) -> None:
        try:
            await self._run(job)
        finally:
            self._active_job_keys.discard(job.job_key)

    async def shutdown(self) -> None:
        self._accepting = False
        tasks = tuple(self._tasks)
        if not tasks:
            await logger.ainfo("[Stickers] Pack processing manager stopped", pending_jobs=0)
            return

        await logger.ainfo(
            "[Stickers] Waiting for pack processing jobs",
            pending_jobs=len(tasks),
            timeout_seconds=_SHUTDOWN_TIMEOUT_SECONDS,
        )
        try:
            async with asyncio.timeout(_SHUTDOWN_TIMEOUT_SECONDS):
                await asyncio.gather(*tasks, return_exceptions=True)
        except TimeoutError:
            await logger.awarning(
                "[Stickers] Cancelling pack processing jobs after shutdown timeout",
                pending_jobs=len(self._tasks),
                timeout_seconds=_SHUTDOWN_TIMEOUT_SECONDS,
            )
            for task in tuple(self._tasks):
                task.cancel()
            await asyncio.gather(*tuple(self._tasks), return_exceptions=True)

        await logger.ainfo("[Stickers] Pack processing manager stopped", pending_jobs=len(self._tasks))

    async def _run(self, job: StickerPackJob) -> None:
        started_at = perf_counter()
        with sentry_sdk.isolation_scope() as scope:
            scope.set_tag("korone.handler", "StickerStealPackHandler")
            scope.set_context("sticker_pack_processing", {"job_id": job.job_id})
            try:
                async with self._concurrency:
                    await logger.ainfo(
                        "[Stickers] Pack processing started",
                        job_id=job.job_id,
                        queue_wait_seconds=round(perf_counter() - job.queued_at, 3),
                    )
                    async with asyncio.timeout(_MAX_JOB_SECONDS):
                        await job.handler(job.event, job.data)
            except asyncio.CancelledError:
                await logger.ainfo("[Stickers] Pack processing cancelled", job_id=job.job_id)
                raise
            except Exception:  # ruff: ignore[blind-except]
                await logger.aexception(
                    "[Stickers] Unhandled pack processing failure",
                    job_id=job.job_id,
                    duration_seconds=round(perf_counter() - started_at, 3),
                )
                await self._reply_safely(job.event, job.failure_text, job.job_id)
            finally:
                await logger.ainfo(
                    "[Stickers] Pack processing finished",
                    job_id=job.job_id,
                    duration_seconds=round(perf_counter() - started_at, 3),
                )

    @staticmethod
    async def _reply_safely(event: Message, text: str, job_id: str) -> None:
        try:
            await reply_message(event, text)
        except TelegramAPIError as error:
            await logger.awarning(
                "[Stickers] Could not report pack processing result", job_id=job_id, error_type=type(error).__name__
            )
