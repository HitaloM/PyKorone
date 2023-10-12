# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar

Result = TypeVar("Result")


async def run_async(func: Callable[..., Result], *args: Any, **kwargs: Any) -> Result:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
