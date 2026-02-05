from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, TypeVar, cast

import ujson

from korone import aredis
from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None

T = TypeVar("T", bound=JsonValue)

_NOT_SET_MARKER = "__korone_not_set__"

logger = get_logger(__name__)


async def set_value(key: str, value: JsonValue, ttl: float | None) -> None:
    wrapped = {"v": value, "s": _NOT_SET_MARKER if value is None else None}
    serialized = ujson.dumps(wrapped)
    await aredis.set(key, serialized)
    if ttl:
        await aredis.expire(key, int(ttl))


def _deserialize(data: bytes | str) -> tuple[JsonValue | None, bool]:
    try:
        parsed = ujson.loads(data)
        if isinstance(parsed, dict) and "v" in parsed:
            return parsed["v"], True
    except ujson.JSONDecodeError, TypeError:
        pass
    return None, False


class Cached[T: JsonValue]:
    def __init__(self, ttl: float | None = None, key: str | None = None, *, no_self: bool = False) -> None:
        self.ttl = ttl
        self.key = key
        self.no_self = no_self
        self.func: Callable[..., Awaitable[T]] | None = None

    def __call__(self, *args: Any, **kwargs: dict[str, Any]) -> Any:
        if self.func is None:
            func = cast("Callable[..., Awaitable[T]]", args[0])
            self.func = func
            functools.update_wrapper(self, func)

            @functools.wraps(func)
            async def wrapper(*w_args: Any, **w_kwargs: dict[str, Any]) -> T:
                return await self._get_or_set(*w_args, **w_kwargs)

            return cast("Callable[..., Awaitable[T]]", wrapper)
        return self._get_or_set(*args, **kwargs)

    async def _get_or_set(self, *args: Any, **kwargs: dict[str, Any]) -> T:
        if self.func is None:
            msg = "Cached decorator not properly initialized"
            raise RuntimeError(msg)

        key = self._build_key(*args, **kwargs)

        cached_data = await aredis.get(key)
        if cached_data is not None:
            value, is_valid = _deserialize(cached_data)
            if is_valid:
                return cast("T", value)

        result = await self.func(*args, **kwargs)
        await set_value(key, cast("JsonValue", result), ttl=self.ttl)
        await logger.adebug("Cached: writing new data", key=key)
        return result

    def _build_key(self, *args: Any, **kwargs: dict[str, Any]) -> str:
        if self.func is None:
            msg = "Cached decorator not properly initialized"
            raise RuntimeError(msg)

        ordered_kwargs = sorted(kwargs.items())

        func_module = getattr(self.func, "__module__", "") or ""
        func_name = getattr(self.func, "__name__", "unknown")
        base_key = self.key or func_module + func_name
        args_key = str(args[1:] if self.no_self else args)

        new_key = base_key + args_key
        if ordered_kwargs:
            new_key += str(ordered_kwargs)

        return new_key

    async def reset_cache(self, *args: Any, new_value: T | None = None, **kwargs: dict[str, Any]) -> int | None:
        key = self._build_key(*args, **kwargs)
        if new_value is not None:
            await set_value(key, cast("JsonValue", new_value), ttl=self.ttl)
            return None
        return await aredis.delete(key)
