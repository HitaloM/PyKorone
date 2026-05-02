from __future__ import annotations

import asyncio
import functools
import math
import random
import time
from typing import TYPE_CHECKING, ParamSpec, TypeVar, cast

import orjson

from korone import aredis
from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None

P = ParamSpec("P")
T = TypeVar("T", bound=JsonValue)

_NOT_SET_MARKER = "__korone_not_set__"
_LOCK_CLEANUP_INTERVAL = 300

logger = get_logger(__name__)
_background_tasks: set[asyncio.Task[None]] = set()


async def set_value(key: str, value: JsonValue, ttl: float | None) -> None:
    expiry_timestamp = time.time() + ttl if ttl else None
    wrapped = {"v": value, "s": _NOT_SET_MARKER if value is None else None, "exp": expiry_timestamp}
    serialized = orjson.dumps(wrapped)
    await aredis.set(key, serialized)
    if ttl:
        await aredis.expire(key, int(ttl))


def _deserialize(data: bytes | str) -> tuple[JsonValue | None, float | None, bool]:
    try:
        parsed = orjson.loads(data)
        if isinstance(parsed, dict) and "v" in parsed:
            return parsed["v"], parsed.get("exp"), True
    except orjson.JSONDecodeError, TypeError:
        pass
    return None, None, False


def _should_early_recompute(expiry: float | None, beta: float) -> bool:
    if expiry is None or beta <= 0:
        return False

    time_until_expiry = expiry - time.time()
    if time_until_expiry <= 0:
        return True

    probability = beta * math.exp(-time_until_expiry / beta)
    return random.random() < probability


def _track_background_task(task: asyncio.Task[None], *, message: str, **context: object) -> None:
    _background_tasks.add(task)

    def _on_done(completed_task: asyncio.Task[None]) -> None:
        _background_tasks.discard(completed_task)
        try:
            error = completed_task.exception()
        except asyncio.CancelledError:
            return
        if error is not None:
            logger.warning(message, error=str(error), **context)

    task.add_done_callback(_on_done)


class _LockEntry:
    __slots__ = ("lock", "waiters")

    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.waiters: int = 0


class _LockRegistry:
    def __init__(self) -> None:
        self._locks: dict[str, _LockEntry] = {}
        self._cleanup_task: asyncio.Task[None] | None = None

    def _ensure_cleanup_task(self) -> None:
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return
            self._cleanup_task = loop.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self) -> None:
        while True:
            await asyncio.sleep(_LOCK_CLEANUP_INTERVAL)
            stale_keys = [key for key, entry in self._locks.items() if entry.waiters <= 0 and not entry.lock.locked()]
            for key in stale_keys:
                self._locks.pop(key, None)
            if stale_keys:
                await logger.adebug("Cached: lock registry cleanup removed stale entries", count=len(stale_keys))

    def acquire_entry(self, key: str) -> _LockEntry:
        self._ensure_cleanup_task()
        entry = self._locks.get(key)
        if entry is None:
            entry = _LockEntry()
            self._locks[key] = entry
        entry.waiters += 1
        return entry

    def release_entry(self, key: str) -> None:
        entry = self._locks.get(key)
        if entry is None:
            return
        entry.waiters -= 1
        if entry.waiters <= 0 and not entry.lock.locked():
            self._locks.pop(key, None)


_lock_registry = _LockRegistry()


class Cached[**P, T: JsonValue]:
    def __init__(
        self,
        ttl: float | None = None,
        key: str | None = None,
        *,
        no_self: bool = False,
        stampede_protection: bool = True,
        early_recompute_beta: float = 1.0,
    ) -> None:
        self.ttl = ttl
        self.key = key
        self.no_self = no_self
        self.stampede_protection = stampede_protection
        self.early_recompute_beta = early_recompute_beta
        self.func: Callable[P, Awaitable[T]] | None = None

    def __call__(self, func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        self.func = func
        functools.update_wrapper(self, func)

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await self._get_or_set(*args, **kwargs)

        return wrapper

    async def _get_or_set(self, *args: P.args, **kwargs: P.kwargs) -> T:
        if self.func is None:
            msg = "Cached decorator not properly initialized"
            raise RuntimeError(msg)

        key = self._build_key(*args, **kwargs)

        cached_data = await aredis.get(key)
        if cached_data is not None:
            value, expiry, is_valid = _deserialize(cached_data)
            if is_valid:
                if self.early_recompute_beta > 0 and _should_early_recompute(expiry, self.early_recompute_beta):
                    background_task = asyncio.create_task(self._recompute_and_store(key, *args, **kwargs))
                    _track_background_task(background_task, message="Cached: PER background refresh failed", key=key)
                return cast("T", value)

        if self.stampede_protection:
            return await self._get_or_set_with_lock(key, *args, **kwargs)

        result = await self.func(*args, **kwargs)
        background_task = asyncio.create_task(set_value(key, result, ttl=self.ttl))
        _track_background_task(background_task, message="Cached: background write failed", key=key)
        await logger.adebug("Cached: writing new data", key=key)
        return result

    async def _get_or_set_with_lock(self, key: str, *args: P.args, **kwargs: P.kwargs) -> T:
        if self.func is None:
            msg = "Cached decorator not properly initialized"
            raise RuntimeError(msg)

        entry = _lock_registry.acquire_entry(key)
        try:
            async with entry.lock:
                cached_data = await aredis.get(key)
                if cached_data is not None:
                    value, _expiry, is_valid = _deserialize(cached_data)
                    if is_valid:
                        return cast("T", value)

                result = await self.func(*args, **kwargs)
                await set_value(key, result, ttl=self.ttl)
                await logger.adebug("Cached: writing new data (lock holder)", key=key)
                return result
        finally:
            _lock_registry.release_entry(key)

    async def _recompute_and_store(self, key: str, *args: P.args, **kwargs: P.kwargs) -> None:
        if self.func is None:
            return

        result = await self.func(*args, **kwargs)
        await set_value(key, result, ttl=self.ttl)
        await logger.adebug("Cached: PER background refresh complete", key=key)

    def _build_key(self, *args: P.args, **kwargs: P.kwargs) -> str:
        if self.func is None:
            msg = "Cached decorator not properly initialized"
            raise RuntimeError(msg)

        ordered_kwargs = sorted(dict(kwargs).items())

        func_module = getattr(self.func, "__module__", "") or ""
        func_name = getattr(self.func, "__name__", "unknown")
        base_key = self.key or func_module + func_name
        args_key = str(args[1:] if self.no_self else args)

        new_key = base_key + args_key
        if ordered_kwargs:
            new_key += str(ordered_kwargs)

        return new_key

    async def reset_cache(self, *args: object, new_value: T | None = None, **kwargs: object) -> int | None:
        if self.func is None:
            msg = "Cached decorator not properly initialized"
            raise RuntimeError(msg)

        ordered_kwargs = sorted(kwargs.items())
        func_module = getattr(self.func, "__module__", "") or ""
        func_name = getattr(self.func, "__name__", "unknown")
        base_key = self.key or func_module + func_name
        args_key = str(args[1:] if self.no_self else args)
        key = base_key + args_key
        if ordered_kwargs:
            key += str(ordered_kwargs)

        if new_value is not None:
            await set_value(key, new_value, ttl=self.ttl)
            return None
        return await aredis.delete(key)
