# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import pickle
from collections.abc import Callable
from datetime import timedelta
from functools import wraps
from typing import Any

from korone import redis


class Cached:
    """
    Decorator class that caches the result of a function using Redis.

    This decorator can be used to cache the result of a function using Redis.
    The cached result will be stored in Redis with a specified time-to-live (TTL).
    If the result is already present in the cache, it will be retrieved from Redis
    and returned without executing the decorated function.
    If the result is not present in the cache, the decorated function will be executed,
    and the result will be stored in Redis for future use.

    Parameters
    ----------
    ttl : timedelta, optional
        Time-to-live for the cached result. Default is 1 hour.

    Examples
    --------
    >>> @Cached(ttl=timedelta(minutes=1))
    ... async def expensive_function(x):
    ...     # Some expensive computation
    ...     return result

    In the above example, the `expensive_function` will be cached using Redis with a TTL of 60
    seconds. Subsequent calls to `expensive_function` with the same arguments will retrieve the
    cached result from Redis instead of executing the function again.
    """

    __slots__ = ("cache", "ttl")

    def __init__(self, ttl: timedelta = timedelta(hours=1)) -> None:
        self.ttl: timedelta = ttl
        self.cache: dict[str, str] = {}

    def __call__(self, func: Callable) -> Callable:
        """
        Decorate a function to cache its result using Redis.

        This method is called when the decorator is applied to a function.
        It returns a decorated function that caches the result of the original function
        using Redis.

        Parameters
        ----------
        func : Callable
            The function to be decorated.

        Returns
        -------
        Callable
            The decorated function.
        """

        @wraps(func)
        async def wrapper(*args: tuple, **kwargs: dict) -> Any:
            cache_key = self.generate_cache_key(func.__name__, args, kwargs)

            cached_result = await redis.get(cache_key)
            if cached_result is not None:
                return pickle.loads(cached_result)

            result = await func(*args, **kwargs)
            packed_value = pickle.dumps(result) or ""
            expire_time = int(self.ttl.total_seconds())
            await redis.set(cache_key, packed_value, expire_time)

            return result

        return wrapper

    async def clear(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Clear the cache for the decorated function.

        Clears the cache for the decorated function by deleting the cached result
        from Redis based on the function name and arguments.

        Parameters
        ----------
        func : Callable
            The decorated function.
        *args : Any
            Positional arguments passed to the decorated function.
        **kwargs : Any
            Keyword arguments passed to the decorated function.
        """
        key = self.generate_cache_key(func.__name__, args, kwargs)
        await redis.delete(key)

    @staticmethod
    def generate_cache_key(name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate a unique cache key based on function name, arguments, and keyword arguments.

        This function takes the name of a function, its positional arguments, and keyword arguments
        and generates a unique cache key based on these inputs. The cache key is a string that
        combines the function name, arguments, and keyword arguments.

        Parameters
        ----------
        name : str
            The name of the function.
        args : tuple
            The positional arguments passed to the function.
        kwargs : dict
            The keyword arguments passed to the function.

        Returns
        -------
        str
            The generated cache key.
        """
        return f"{name}:{args}:{kwargs}"
