import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, override

from aiogram.fsm.storage.redis import RedisEventIsolation
from redis.asyncio.lock import Lock
from redis.exceptions import LockError, LockNotOwnedError, RedisError

from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from aiogram.fsm.storage.base import StorageKey

logger = get_logger(__name__)


class RenewableRedisEventIsolation(RedisEventIsolation):
    @asynccontextmanager
    @override
    async def lock(self, key: StorageKey) -> AsyncGenerator[None]:
        redis_key = self.key_builder.build(key, "lock")
        lock = self.redis.lock(name=redis_key, **self.lock_kwargs, lock_class=Lock)

        if not await lock.acquire():
            msg = "Blocking FSM lock acquisition returned without ownership"
            raise LockError(msg)

        renewal_task = asyncio.create_task(self._renew_lock(lock, redis_key), name=f"fsm-lock-renewal:{redis_key}")
        try:
            yield
        finally:
            renewal_task.cancel()
            await asyncio.gather(renewal_task, return_exceptions=True)
            await self._release_lock(lock, redis_key)

    @staticmethod
    async def _renew_lock(lock: Lock, redis_key: str) -> None:
        timeout = lock.timeout
        if timeout is None:
            return

        while True:
            try:
                await asyncio.sleep(timeout / 3)
                await lock.reacquire()
                await logger.adebug("FSM event isolation lock renewed", redis_key=redis_key, ttl_seconds=timeout)
            except asyncio.CancelledError:
                raise
            except (LockError, RedisError) as error:
                await logger.aerror(
                    "FSM event isolation lock renewal failed", redis_key=redis_key, error_type=type(error).__name__
                )
                return

    @staticmethod
    async def _release_lock(lock: Lock, redis_key: str) -> None:
        try:
            await lock.release()
        except LockNotOwnedError:
            await logger.aerror("FSM event isolation lock expired before release", redis_key=redis_key)
        except RedisError as error:
            await logger.awarning(
                "FSM event isolation lock release failed", redis_key=redis_key, error_type=type(error).__name__
            )
