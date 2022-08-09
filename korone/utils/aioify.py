# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import asyncio
import functools
from typing import Any, Callable, TypeVar

Result = TypeVar("Result")


async def run_async(func: Callable[..., Result], *args: Any, **kwargs: Any) -> Result:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
