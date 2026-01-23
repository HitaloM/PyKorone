from __future__ import annotations

import functools
from typing import Any, Awaitable, Callable, Generic, ParamSpec, TypeVar, Union, overload

import ujson

from korone import aredis
from korone.logging import get_logger

T = TypeVar("T")
P = ParamSpec("P")

_NOT_SET_MARKER = "__korone_not_set__"

logger = get_logger(__name__)


async def set_value(key: str, value: Any, ttl: int | float | None) -> None:
    wrapped = {"v": value, "s": _NOT_SET_MARKER if value is None else None}
    serialized = ujson.dumps(wrapped)
    await aredis.set(key, serialized)
    if ttl:
        await aredis.expire(key, int(ttl))


def _deserialize(data: bytes | str) -> tuple[Any, bool]:
    try:
        parsed = ujson.loads(data)
        if isinstance(parsed, dict) and "v" in parsed:
            return parsed["v"], True
        return None, False
    except ujson.JSONDecodeError, TypeError:
        return None, False


class cached(Generic[T]):
    def __init__(self, ttl: int | float | None = None, key: str | None = None, no_self: bool = False) -> None:
        self.ttl = ttl
        self.key = key
        self.no_self = no_self
        self.func: Callable[..., Awaitable[T]] | None = None

    @overload
    def __call__(self, func: Callable[P, Awaitable[T]]) -> "cached[T]": ...

    @overload
    def __call__(self, *args: Any, **kwargs: Any) -> Awaitable[T]: ...

    def __call__(self, *args: Any, **kwargs: Any) -> Union["cached[T]", Awaitable[T]]:
        if self.func is None:
            self.func = args[0]
            functools.update_wrapper(self, self.func)
            return self
        return self._get_or_set(*args, **kwargs)

    async def _get_or_set(self, *args: Any, **kwargs: Any) -> Any:
        if self.func is None:
            raise RuntimeError("cached decorator not properly initialized")

        key = self._build_key(*args, **kwargs)

        cached_data = await aredis.get(key)
        if cached_data is not None:
            value, is_valid = _deserialize(cached_data)
            if is_valid:
                return value

        result = await self.func(*args, **kwargs)
        await set_value(key, result, ttl=self.ttl)
        await logger.adebug("Cached: writing new data", key=key)
        return result

    def _build_key(self, *args: Any, **kwargs: Any) -> str:
        if self.func is None:
            raise RuntimeError("cached decorator not properly initialized")

        ordered_kwargs = sorted(kwargs.items())

        func_module = getattr(self.func, "__module__", "") or ""
        func_name = getattr(self.func, "__name__", "unknown")
        base_key = self.key if self.key else func_module + func_name
        args_key = str(args[1:] if self.no_self else args)

        new_key = base_key + args_key
        if ordered_kwargs:
            new_key += str(ordered_kwargs)

        return new_key

    async def reset_cache(self, *args: Any, new_value: Any = None, **kwargs: Any) -> int | None:
        key = self._build_key(*args, **kwargs)
        if new_value is not None:
            await set_value(key, new_value, ttl=self.ttl)
            return None
        return await aredis.delete(key)
