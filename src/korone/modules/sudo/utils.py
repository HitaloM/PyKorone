# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html
import io
from subprocess import PIPE
from typing import Any, TypedDict

from anyio import run_process
from hydrogram.types import Message


class CommitInfo(TypedDict):
    title: str


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
