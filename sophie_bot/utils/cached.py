# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import asyncio
import functools
from typing import Any, Awaitable, Callable, TypeVar, Union

import ujson

from sophie_bot.services.redis import aredis
from sophie_bot.utils.logger import log

T = TypeVar("T")

# Sentinel value to distinguish cached None from cache miss
_NOT_SET_MARKER = "__sophie_not_set__"


async def set_value(key: str, value: Any, ttl: int | float | None) -> None:
    """Serialize and store a value in Redis with optional TTL."""
    # Wrap value to distinguish None from cache miss
    wrapped = {"v": value, "s": _NOT_SET_MARKER if value is None else None}
    serialized = ujson.dumps(wrapped)
    await aredis.set(key, serialized)
    if ttl:
        await aredis.expire(key, int(ttl))


def _deserialize(data: bytes | str) -> tuple[Any, bool]:
    """Deserialize cached data. Returns (value, is_valid)."""
    try:
        parsed = ujson.loads(data)
        if isinstance(parsed, dict) and "v" in parsed:
            return parsed["v"], True
        # Legacy format or invalid - treat as cache miss
        return None, False
    except (ujson.JSONDecodeError, TypeError):
        return None, False


class cached:
    """Async caching decorator using Redis with JSON serialization.

    Usage:
        @cached(ttl=300)
        async def get_user(user_id: int) -> dict:
            return await fetch_user(user_id)

        # Reset cache for specific args
        await get_user.reset_cache(user_id, new_value=updated_user)
    """

    def __init__(
        self,
        ttl: int | float | None = None,
        key: str | None = None,
        no_self: bool = False,
    ) -> None:
        self.ttl = ttl
        self.key = key
        self.no_self = no_self
        self.func: Callable[..., Awaitable[T]] | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> Union["cached", Awaitable[T]]:
        if self.func is None:
            # First call - receiving the decorated function
            self.func = args[0]
            functools.update_wrapper(self, self.func)
            return self
        # Subsequent calls - executing the cached function
        return self._get_or_set(*args, **kwargs)

    async def _get_or_set(self, *args: Any, **kwargs: Any) -> Any:
        """Get value from cache or compute and store it."""
        if self.func is None:
            raise RuntimeError("cached decorator not properly initialized")

        key = self._build_key(*args, **kwargs)

        cached_data = await aredis.get(key)
        if cached_data is not None:
            value, is_valid = _deserialize(cached_data)
            if is_valid:
                return value

        # Cache miss - compute value
        result = await self.func(*args, **kwargs)
        asyncio.ensure_future(set_value(key, result, ttl=self.ttl))
        log.debug("Cached: writing new data", key=key)
        return result

    def _build_key(self, *args: Any, **kwargs: Any) -> str:
        """Build a unique cache key from function name and arguments."""
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
        """Reset cache for specific arguments, optionally setting a new value.

        Args:
            *args: Same arguments as the cached function
            new_value: Optional new value to cache
            **kwargs: Same keyword arguments as the cached function

        Returns:
            Number of keys deleted, or None if new_value was set
        """
        key = self._build_key(*args, **kwargs)
        if new_value is not None:
            await set_value(key, new_value, ttl=self.ttl)
            return None
        return await aredis.delete(key)
