# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import asyncio
from asyncio.subprocess import Process
from typing import Tuple


async def shell_exec(code: str, treat=True) -> Tuple[bytes, Process]:
    process = await asyncio.create_subprocess_shell(
        code, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    stdout = (await process.communicate())[0]
    if treat:
        stdout = stdout.decode().strip()
    return stdout, process
