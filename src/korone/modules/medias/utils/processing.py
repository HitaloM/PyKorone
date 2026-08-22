import asyncio
import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Any

import sentry_sdk
from aiogram.types import TelegramObject
from redis.exceptions import LockError, LockNotOwnedError, RedisError

from korone import aredis
from korone.config import CONFIG
from korone.logger import get_logger

if TYPE_CHECKING:
    from redis.asyncio.lock import Lock

    from korone.modules.medias.utils.types import MediaRequest

logger = get_logger(__name__)

_MEDIA_LOCK_PREFIX = "korone:media-processing"

type MediaHandlerCallback = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


def media_source_id(source_url: str) -> str:
    return hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:16]


def _media_lock_name(source_url: str) -> str:
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()
    return f"{_MEDIA_LOCK_PREFIX}:{digest}"


@dataclass(frozen=True, slots=True)
class MediaJob:
    handler: MediaHandlerCallback
    event: TelegramObject
    data: dict[str, Any]
    handler_name: str
    request: MediaRequest
    queued_at: float

    @property
    def source_id(self) -> str:
        return media_source_id(self.request.url)


class MediaProcessingManager:
    def __init__(self) -> None:
        self._accepting = False
        self._tasks: set[asyncio.Task[None]] = set()
        self._concurrency = asyncio.Semaphore(CONFIG.media_max_concurrent_jobs)

    async def start(self) -> None:
        self._accepting = True
        await logger.ainfo(
            "[Medias] Processing manager started",
            max_concurrent_jobs=CONFIG.media_max_concurrent_jobs,
            max_pending_jobs=CONFIG.media_max_pending_jobs,
        )

    async def submit(self, job: MediaJob) -> bool:
        if not self._accepting:
            await logger.awarning(
                "[Medias] Processing rejected while shutting down", handler=job.handler_name, source_id=job.source_id
            )
            return False

        if len(self._tasks) >= CONFIG.media_max_pending_jobs:
            await logger.awarning(
                "[Medias] Processing capacity exhausted",
                handler=job.handler_name,
                source_id=job.source_id,
                pending_jobs=len(self._tasks),
                max_pending_jobs=CONFIG.media_max_pending_jobs,
            )
            return False

        task = asyncio.create_task(self._run(job), name=f"media:{job.handler_name}:{job.source_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return True

    async def shutdown(self) -> None:
        self._accepting = False
        tasks = tuple(self._tasks)
        if not tasks:
            await logger.ainfo("[Medias] Processing manager stopped", pending_jobs=0)
            return

        await logger.ainfo(
            "[Medias] Waiting for processing jobs",
            pending_jobs=len(tasks),
            timeout_seconds=CONFIG.media_shutdown_timeout,
        )
        try:
            async with asyncio.timeout(CONFIG.media_shutdown_timeout):
                await asyncio.gather(*tasks, return_exceptions=True)
        except TimeoutError:
            await logger.awarning(
                "[Medias] Cancelling processing jobs after shutdown timeout",
                pending_jobs=len(self._tasks),
                timeout_seconds=CONFIG.media_shutdown_timeout,
            )
            for task in tuple(self._tasks):
                task.cancel()
            await asyncio.gather(*tuple(self._tasks), return_exceptions=True)

        await logger.ainfo("[Medias] Processing manager stopped", pending_jobs=len(self._tasks))

    async def _run(self, job: MediaJob) -> None:
        started_at = perf_counter()
        with sentry_sdk.isolation_scope() as scope:
            scope.set_tag("korone.handler", job.handler_name)
            scope.set_tag("korone.fsm_isolation", "disabled")
            scope.set_tag("korone.media_lock", "redis_url")
            scope.set_context("media_processing", self._processing_context(job))

            try:
                await self._run_with_lock(job, scope)
            except asyncio.CancelledError:
                await logger.ainfo("[Medias] Processing cancelled", handler=job.handler_name, source_id=job.source_id)
                raise
            except Exception:  # ruff: ignore[blind-except]
                await logger.aexception(
                    "[Medias] Unhandled processing failure", handler=job.handler_name, source_id=job.source_id
                )
            finally:
                await logger.ainfo(
                    "[Medias] Processing finished",
                    handler=job.handler_name,
                    source_id=job.source_id,
                    duration_seconds=round(perf_counter() - started_at, 3),
                )

    @staticmethod
    def _processing_context(job: MediaJob) -> dict[str, object]:
        return {
            "handler": job.handler_name,
            "provider": job.request.provider.name,
            "source_id": job.source_id,
            "fsm_isolation": "disabled",
            "lock": "redis_url",
        }

    async def _run_handler(self, job: MediaJob, scope: sentry_sdk.Scope) -> None:
        async with self._concurrency:
            queue_wait_seconds = perf_counter() - job.queued_at
            scope.set_context(
                "media_processing", self._processing_context(job) | {"queue_wait_seconds": round(queue_wait_seconds, 3)}
            )
            await logger.ainfo(
                "[Medias] Processing started",
                handler=job.handler_name,
                source_id=job.source_id,
                pending_jobs=len(self._tasks),
                queue_wait_seconds=round(queue_wait_seconds, 3),
            )
            await job.handler(job.event, job.data)

    async def _run_with_lock(self, job: MediaJob, scope: sentry_sdk.Scope) -> None:
        lock = aredis.lock(_media_lock_name(job.request.url), timeout=CONFIG.media_processing_lock_timeout)
        try:
            acquired = await lock.acquire()
        except asyncio.CancelledError:
            raise
        except RedisError as error:
            scope.set_tag("korone.media_lock", "unavailable")
            await logger.awarning(
                "[Medias] Redis processing lock unavailable; continuing without deduplication",
                handler=job.handler_name,
                source_id=job.source_id,
                error_type=type(error).__name__,
            )
            await self._run_handler(job, scope)
            return

        scope.set_context(
            "media_lock",
            {"kind": "redis_url", "source_id": job.source_id, "ttl_seconds": CONFIG.media_processing_lock_timeout},
        )

        if not acquired:
            msg = "Blocking Redis lock acquisition returned without ownership"
            raise RuntimeError(msg)

        lock_lost = asyncio.Event()
        renewal_task = asyncio.create_task(
            self._renew_lock(lock, lock_lost, job), name=f"media-lock-renewal:{job.source_id}"
        )
        try:
            await self._run_handler(job, scope)
        finally:
            renewal_task.cancel()
            await asyncio.gather(renewal_task, return_exceptions=True)
            await self._release_lock(lock, lock_lost, job)

    @staticmethod
    async def _renew_lock(lock: Lock, lock_lost: asyncio.Event, job: MediaJob) -> None:
        renewal_interval = CONFIG.media_processing_lock_timeout / 3
        while True:
            try:
                await asyncio.sleep(renewal_interval)
                await lock.reacquire()
            except asyncio.CancelledError:
                raise
            except (LockError, RedisError) as error:
                lock_lost.set()
                await logger.aerror(
                    "[Medias] Processing lock renewal failed",
                    handler=job.handler_name,
                    source_id=job.source_id,
                    error_type=type(error).__name__,
                )
                return

    @staticmethod
    async def _release_lock(lock: Lock, lock_lost: asyncio.Event, job: MediaJob) -> None:
        if lock_lost.is_set():
            await logger.awarning(
                "[Medias] Processing lock ownership lost; release skipped",
                handler=job.handler_name,
                source_id=job.source_id,
            )
            return

        try:
            await lock.release()
        except LockNotOwnedError:
            await logger.aerror(
                "[Medias] Processing lock expired before release", handler=job.handler_name, source_id=job.source_id
            )
            return
        except RedisError as error:
            await logger.awarning(
                "[Medias] Processing lock release failed",
                handler=job.handler_name,
                source_id=job.source_id,
                error_type=type(error).__name__,
            )
            return
