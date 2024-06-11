# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar

Result = TypeVar("Result")


async def run_sync(func: Callable[..., Result], *args: Any, **kwargs: Any) -> Result:
    """
    Executes a synchronous function in an asynchronous event loop.

    This function provides a mechanism to run a synchronous (blocking) function
    asynchronously by scheduling its execution in a separate thread or process. This is
    particularly useful for integrating blocking I/O operations or computationally
    intensive functions into an asynchronous application without blocking the event loop.

    The function to be executed, along with its arguments, is wrapped using `functools.partial`
    to create a callable object that requires no arguments. This callable is then passed to
    `asyncio.get_event_loop().run_in_executor`, which schedules its execution in the default
    executor (a thread pool). The caller of `run_sync` awaits the completion of the callable,
    allowing other asynchronous tasks to run concurrently.

    Parameters
    ----------
    func : Callable[..., Result]
        A synchronous function that performs a blocking operation. This function
        can return a result, which will be passed back to the caller of `run_sync`.
    *args : Any
        Positional arguments to be passed to `func`.
    **kwargs : Any
        Keyword arguments to be passed to `func`.

    Returns
    -------
    Result
        The result returned by `func`. The type of this result is determined by the
        return type of `func`.

    Notes
    -----
    The default executor used by `run_in_executor` is a thread pool, which means that
    `func` will be executed in a separate thread. This is suitable for I/O-bound tasks
    but may not provide significant performance benefits for CPU-bound tasks due to the
    Global Interpreter Lock (GIL) in CPython.

    Examples
    --------
    >>> import time
    >>> async def async_main():
    ...     result = await run_sync(time.sleep, 1, result=42)
    ...     print(result)
    >>> asyncio.run(async_main())
    42
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
