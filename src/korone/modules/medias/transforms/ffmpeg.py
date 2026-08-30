import asyncio
import contextlib
from typing import TYPE_CHECKING

import aiofiles
import aiofiles.os

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


async def _stop_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return

    with contextlib.suppress(ProcessLookupError):
        process.terminate()
    try:
        async with asyncio.timeout(5):
            await process.wait()
    except TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            process.kill()
        await process.wait()


class FFmpegTranscoder:
    __slots__ = ("_slots",)

    def __init__(self, slots: asyncio.Semaphore) -> None:
        self._slots = slots

    async def run_to_payload(
        self, command: Sequence[str], output_path: Path, *, timeout_seconds: float, max_size: int | None
    ) -> bytes | None:
        async with self._slots:
            try:
                process = await asyncio.create_subprocess_exec(
                    *command, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
                )
            except OSError:
                return None

            try:
                async with asyncio.timeout(timeout_seconds):
                    await process.communicate()
            except asyncio.CancelledError:
                await _stop_process(process)
                raise
            except TimeoutError:
                await _stop_process(process)
                return None

        if process.returncode != 0:
            return None
        try:
            output_size = (await aiofiles.os.stat(output_path)).st_size
        except FileNotFoundError:
            return None
        if max_size is not None and output_size > max_size:
            return None

        async with aiofiles.open(output_path, "rb") as output_file:
            payload = await output_file.read() if max_size is None else await output_file.read(max_size + 1)
        return None if max_size is not None and len(payload) > max_size else payload
