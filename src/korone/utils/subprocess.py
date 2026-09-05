import asyncio
from contextlib import suppress
from subprocess import CompletedProcess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


async def _stop_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    with suppress(ProcessLookupError):
        process.terminate()
    try:
        async with asyncio.timeout(5):
            await process.communicate()
    except TimeoutError:
        with suppress(ProcessLookupError):
            process.kill()
        await process.communicate()


async def run_process(
    command: Sequence[str], *, timeout_seconds: float, stdout: int = asyncio.subprocess.PIPE
) -> CompletedProcess[bytes]:
    process = await asyncio.create_subprocess_exec(*command, stdout=stdout, stderr=asyncio.subprocess.PIPE)
    try:
        async with asyncio.timeout(timeout_seconds):
            output, errors = await process.communicate()
    except BaseException:
        await _stop_process(process)
        raise
    if process.returncode is None:
        msg = "Subprocess completed without an exit status"
        raise RuntimeError(msg)
    return CompletedProcess(command, process.returncode, output, errors)
