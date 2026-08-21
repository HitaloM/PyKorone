import asyncio
import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter
from typing import TYPE_CHECKING, Any, Final

import sentry_sdk
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message, TelegramObject
from redis.exceptions import LockNotOwnedError, RedisError

from korone import aredis
from korone.logger import get_logger

if TYPE_CHECKING:
    from redis.asyncio.lock import Lock

logger = get_logger(__name__)

_LOCK_PREFIX: Final = "korone:sticker-pack-processing"
_LOCK_TIMEOUT_SECONDS: Final = 90.0
_MAX_CONCURRENT_JOBS: Final = 2
_MAX_PENDING_JOBS: Final = 32
_MAX_JOB_SECONDS: Final = 30 * 60
_SHUTDOWN_TIMEOUT_SECONDS: Final = 30

type StickerPackHandler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class StickerPackSubmission(StrEnum):
    ACCEPTED = "accepted"
    BUSY = "busy"


class StickerPackLockLostError(RuntimeError):
    pass


def sticker_pack_job_key(user_id: int, pack_title: str) -> str:
    digest = hashlib.sha256(f"{user_id}:{pack_title.lower()}".encode()).hexdigest()
    return f"{_LOCK_PREFIX}:{digest}"


@dataclass(frozen=True, slots=True)
class StickerPackJob:
    handler: StickerPackHandler
    event: Message
    data: dict[str, Any]
    job_key: str
    job_id: str
    queued_at: float
    duplicate_text: str
    failure_text: str


class StickerPackProcessingManager:
    def __init__(self) -> None:
        self._accepting = False
        self._tasks: set[asyncio.Task[None]] = set()
        self._concurrency = asyncio.Semaphore(_MAX_CONCURRENT_JOBS)

    async def start(self) -> None:
        self._accepting = True
        await logger.ainfo(
            "[Stickers] Pack processing manager started",
            max_concurrent_jobs=_MAX_CONCURRENT_JOBS,
            max_pending_jobs=_MAX_PENDING_JOBS,
        )

    async def submit(self, job: StickerPackJob) -> StickerPackSubmission:
        if not self._accepting or len(self._tasks) >= _MAX_PENDING_JOBS:
            await logger.awarning(
                "[Stickers] Pack processing rejected",
                job_id=job.job_id,
                accepting=self._accepting,
                pending_jobs=len(self._tasks),
            )
            return StickerPackSubmission.BUSY

        task = asyncio.create_task(self._run(job), name=f"sticker-pack:{job.job_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return StickerPackSubmission.ACCEPTED

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
            scope.set_tag("korone.fsm_isolation", "disabled")
            scope.set_tag("korone.sticker_pack_lock", "redis_user_pack")
            scope.set_context(
                "sticker_pack_processing",
                {"job_id": job.job_id, "fsm_isolation": "disabled", "lock": "redis_user_pack"},
            )
            try:
                async with self._concurrency:
                    await logger.ainfo(
                        "[Stickers] Pack processing started",
                        job_id=job.job_id,
                        queue_wait_seconds=round(perf_counter() - job.queued_at, 3),
                    )
                    await self._run_with_lock(job)
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

    async def _run_with_lock(self, job: StickerPackJob) -> None:
        lock = aredis.lock(job.job_key, timeout=_LOCK_TIMEOUT_SECONDS, blocking=False)
        try:
            acquired = await lock.acquire()
        except RedisError as error:
            await logger.aerror(
                "[Stickers] Pack processing lock unavailable", job_id=job.job_id, error_type=type(error).__name__
            )
            await self._reply_safely(job.event, job.failure_text, job.job_id)
            return

        if not acquired:
            await logger.ainfo("[Stickers] Duplicate pack processing rejected", job_id=job.job_id)
            await self._reply_safely(job.event, job.duplicate_text, job.job_id)
            return

        completed = asyncio.Event()
        try:
            async with asyncio.TaskGroup() as task_group:
                task_group.create_task(self._execute(job, completed), name=f"sticker-pack-work:{job.job_id}")
                task_group.create_task(
                    self._renew_lock(lock, completed, job.job_id), name=f"sticker-pack-lock:{job.job_id}"
                )
        finally:
            await self._release_lock(lock, job.job_id)

    @staticmethod
    async def _execute(job: StickerPackJob, completed: asyncio.Event) -> None:
        try:
            async with asyncio.timeout(_MAX_JOB_SECONDS):
                await job.handler(job.event, job.data)
        finally:
            completed.set()

    @staticmethod
    async def _renew_lock(lock: Lock, completed: asyncio.Event, job_id: str) -> None:
        renewal_interval = _LOCK_TIMEOUT_SECONDS / 3
        while not completed.is_set():
            try:
                async with asyncio.timeout(renewal_interval):
                    await completed.wait()
                    return
            except TimeoutError:
                pass

            try:
                await lock.reacquire()
            except RedisError as error:
                msg = "Sticker pack lock ownership was lost during processing"
                raise StickerPackLockLostError(msg) from error

            await logger.adebug(
                "[Stickers] Pack processing lock renewed", job_id=job_id, ttl_seconds=_LOCK_TIMEOUT_SECONDS
            )

    @staticmethod
    async def _release_lock(lock: Lock, job_id: str) -> None:
        try:
            await lock.release()
        except LockNotOwnedError:
            await logger.aerror("[Stickers] Pack processing lock expired before release", job_id=job_id)
        except RedisError as error:
            await logger.awarning(
                "[Stickers] Pack processing lock release failed", job_id=job_id, error_type=type(error).__name__
            )

    @staticmethod
    async def _reply_safely(event: Message, text: str, job_id: str) -> None:
        try:
            await event.reply(text)
        except TelegramAPIError as error:
            await logger.awarning(
                "[Stickers] Could not report pack processing result", job_id=job_id, error_type=type(error).__name__
            )
