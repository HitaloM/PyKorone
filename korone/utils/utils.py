# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import html
import math
import os
import platform
import sys
from functools import partial, wraps
from typing import Callable

import httpx
from pyrogram import Client
from pyrogram.errors import ChatWriteForbidden
from pyrogram.types import Message

# unique session of httpx
timeout = httpx.Timeout(40, pool=None)
http = httpx.AsyncClient(http2=True, timeout=timeout)


# Misc
def pretty_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def leave_if_muted(func: Callable) -> Callable:
    @wraps(func)
    async def leave(c: Client, m: Message, *args, **kwargs):
        try:
            await func(c, m, *args, **kwargs)
        except ChatWriteForbidden:
            await c.leave_chat(m.chat.id)
            await c.send_log(
                (
                    f"Eu saí do grupo <b>{html.escape(m.chat.title)}</b>"
                    " (<code>{m.chat.id}</code>) por terem me silenciado."
                ),
                disable_notification=False,
                disable_web_page_preview=True,
            )

    return leave


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
