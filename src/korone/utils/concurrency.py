# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from functools import partial
from os import cpu_count
from typing import TYPE_CHECKING, Any, Final

from anyio import CapacityLimiter, to_thread

if TYPE_CHECKING:
    from collections.abc import Callable

_DEFAULT_THREAD_TOKENS: Final[int] = max(16, min(64, (cpu_count() or 1) * 5))
BLOCKING_CALLS_LIMITER: Final[CapacityLimiter] = CapacityLimiter(_DEFAULT_THREAD_TOKENS)


async def run_blocking[R](
    func: Callable[..., R],
    /,
    *args: Any,
    limiter: CapacityLimiter | None = None,
    cancellable: bool = False,
    abandon_on_cancel: bool = False,
    **kwargs: Any,
) -> R:
    """Run a blocking callable in a worker thread.

    This helper centralizes the recommended ``anyio.to_thread.run_sync`` pattern so
    that blocking work never monopolizes the event loop and remains constrained by a
    shared :class:`~anyio.CapacityLimiter`.

    Args:
        func: Synchronous callable to execute off the event loop thread.
        *args: Positional arguments passed to ``func``.
        limiter: Optional limiter overriding the shared blocking limiter.
        cancellable: Whether awaiting the result should be cancellable.
        abandon_on_cancel: Whether the worker thread may continue running after a
            cancellation. See ``anyio.to_thread.run_sync``.
        **kwargs: Keyword arguments passed to ``func``.

    Returns:
        The return value from ``func``.
    """

    effective_limiter = limiter or BLOCKING_CALLS_LIMITER
    bound = func if not (args or kwargs) else partial(func, *args, **kwargs)

    return await to_thread.run_sync(
        bound,
        limiter=effective_limiter,
        cancellable=cancellable,
        abandon_on_cancel=abandon_on_cancel,
    )
