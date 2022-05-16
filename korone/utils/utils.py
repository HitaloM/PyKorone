# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import asyncio
import math
import os
import platform
import sys
from functools import partial, wraps
from typing import Callable, Iterable

import httpx
from pyrogram import Client
from pyrogram.types import Message

# unique session of httpx
timeout = httpx.Timeout(40, pool=None)
http = httpx.AsyncClient(http2=True, timeout=timeout, follow_redirects=True)


# Misc
def pretty_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name: Iterable[str] = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def aiowrap(func: Callable) -> Callable:
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


async def shell_exec(code, treat=True):
    process = await asyncio.create_subprocess_shell(
        code, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    stdout = (await process.communicate())[0]
    if treat:
        stdout = stdout.decode().strip()
    return stdout, process


# Sysutils
def is_windows() -> bool:
    return bool(
        platform.system().lower() == "windows"
        or os.name == "nt"
        or sys.platform.startswith("win")
    )


async def client_restart(c: Client, m: Message):
    await c.restart()
    await m.edit("Reiniciado!")
