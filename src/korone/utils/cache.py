# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import pickle
from collections.abc import Callable
from datetime import timedelta
from functools import wraps
from typing import Any

from korone import redis


def generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate a unique cache key based on function name, arguments, and keyword arguments.

    This function takes the name of a function, its positional arguments, and keyword arguments
    and generates a unique cache key based on these inputs. The cache key is a string that
    combines the function name, arguments, and keyword arguments.

    Parameters
    ----------
    func_name : str
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
    return f"{func_name}:{args}:{kwargs}"


def cached(ttl: timedelta = timedelta(hours=1)) -> Callable[[Callable], Callable]:
    """
    Decorator that caches the result of a function using Redis.

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

    Returns
    -------
    function
        Decorated function with caching functionality.

    Examples
    --------
    >>> @cached(ttl=timedelta(minutes=1))
    ... def expensive_function(x):
    ...     # Some expensive computation
    ...     return result

    In the above example, the `expensive_function` will be cached using Redis with a TTL of 60
    seconds. Subsequent calls to `expensive_function` with the same arguments will retrieve the
    cached result from Redis instead of executing the function again.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: tuple, **kwargs: dict) -> Any:
            """
            The wrapper function that checks if the result is already in the cache.

            Wrapper function that checks if the result is already in the cache,
            executes the function if not, and stores the result in the cache.

            Parameters
            ----------
            *args : tuple
                Positional arguments passed to the decorated function.
            **kwargs : dict
                Keyword arguments passed to the decorated function.

            Returns
            -------
            Any
                Result of the decorated function.
            """
            cache_key = generate_cache_key(func.__name__, args, kwargs)

            cached_result = await redis.get(cache_key)
            if cached_result is not None:
                return pickle.loads(cached_result)

            result = await func(*args, **kwargs)
            packed_value: bytes | str = pickle.dumps(result) or ""
            expire_time = int(ttl.total_seconds())
            await redis.set(cache_key, packed_value, expire_time)

            return result

        @wraps(func)
        async def clear(*args: tuple, **kwargs: dict) -> None:
            """
            Clear the cache for the decorated function.

            Clears the cache for the decorated function by deleting the cached result
            from Redis based on the function name and arguments.

            Parameters
            ----------
            *args : tuple
                Positional arguments passed to the decorated function.
            **kwargs : dict
                Keyword arguments passed to the decorated function.
            """
            key = generate_cache_key(func.__name__, args, kwargs)
            await redis.delete(key)

        setattr(wrapper, "clear", clear)

        return wrapper

    return decorator
