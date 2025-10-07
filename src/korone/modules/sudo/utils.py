# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html
import io
import os
import sys
import time
from subprocess import PIPE
from typing import Any, Never, TypedDict

from anyio import run_process
from hydrogram.types import Message

from korone import constants
from korone.utils.caching import cache


class CommitInfo(TypedDict):
    title: str


class RebootCache(TypedDict):
    chat_id: int
    message_id: int
    time: float


async def generate_document(output: Any, message: Message) -> None:
    with io.BytesIO(str.encode(str(output))) as file:
        file.name = "output.txt"
        caption = "Output is too large to be sent as a text message."
        await message.reply_document(file, caption=caption)


async def run_command(command: str) -> str:
    result = await run_process(command, stdout=PIPE, stderr=PIPE)
    stdout = result.stdout or b""
    stderr = result.stderr or b""
    return (stdout + stderr).decode()


async def fetch_updates() -> str:
    await run_command("git fetch origin")
    return await run_command("git log HEAD..origin/main --oneline")


def parse_commits(stdout: str) -> dict[str, CommitInfo]:
    return {
        parts[0]: {"title": parts[1]}
        for line in stdout.split("\n")
        if line
        for parts in [line.split(" ", 1)]
    }


def generate_changelog(commits: dict[str, CommitInfo]) -> str:
    return (
        "<b>Changelog</b>:\n"
        + "\n".join(
            f"  - [<code>{c_hash[:7]}</code>] {html.escape(commit['title'])}"
            for c_hash, commit in commits.items()
        )
        + f"\n\n<b>New commits count</b>: <code>{len(commits)}</code>."
    )


async def perform_update() -> str:
    commands = ["git reset --hard origin/main", "pybabel compile -d locales -D bot", "uv sync"]
    return "".join([await run_command(command) for command in commands])


async def restart_bot(message: Message, text: str) -> Never:
    await cache.delete(constants.REBOOT_CACHE_KEY)
    await message.edit_text(text)

    value: RebootCache = {
        "chat_id": message.chat.id,
        "message_id": message.id,
        "time": time.time(),
    }
    await cache.set(constants.REBOOT_CACHE_KEY, value=value, expire=constants.REBOOT_CACHE_TTL)

    main_module = sys.modules.get("__main__")
    module_name = None

    if main_module is not None:
        if package_name := getattr(main_module, "__package__", None):
            module_name = package_name
        elif (spec := getattr(main_module, "__spec__", None)) and (
            spec_name := getattr(spec, "name", None)
        ):
            module_name = spec_name.removesuffix(".__main__")

    if module_name:
        args = [sys.executable, "-m", module_name, *sys.argv[1:]]
    else:
        script_candidate = sys.argv[0] or getattr(main_module, "__file__", "")
        args = [sys.executable, script_candidate, *sys.argv[1:]]

    os.execv(sys.executable, args)
