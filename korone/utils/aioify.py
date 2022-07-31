# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

thread_pool = ThreadPoolExecutor()


async def run_async(function, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, partial(function, *args))
