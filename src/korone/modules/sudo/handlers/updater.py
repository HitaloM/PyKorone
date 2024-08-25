# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import html

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import CallbackQuery, Message

from korone import cache
from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.modules.sudo.callback_data import UpdateCallbackData
from korone.modules.sudo.utils import generate_document, run_command


@router.message(Command(commands=["update", "upgrade"], disableable=False) & IsSudo)
async def update_command(client: Client, message: Message) -> None:
    sent = await message.reply("Checking for updates...")

    try:
        await run_command("git fetch origin")
        stdout = await run_command("git log HEAD..origin/main --oneline")
    except Exception as e:
        await sent.edit(f"An error occurred:\n<code>{e}</code>")
        return

    if not stdout.strip():
        await sent.edit("There is nothing to update.")
        return

    commits = {
        parts[0]: {"title": parts[1]}
        for line in stdout.split("\n")
        if line
        for parts in [line.split(" ", 1)]
    }

    changelog = (
        "<b>Changelog</b>:\n"
        + "\n".join(
            f"  - [<code>{c_hash[:7]}</code>] {html.escape(commit["title"])}"
            for c_hash, commit in commits.items()
        )
        + f"\n\n<b>New commits count</b>: <code>{len(commits)}</code>."
    )

    keyboard = InlineKeyboardBuilder().button(text="🆕 Update", callback_data=UpdateCallbackData())
    await sent.edit(changelog, reply_markup=keyboard.as_markup())


@router.callback_query(UpdateCallbackData.filter() & IsSudo)
async def update_callback(client: Client, callback: CallbackQuery) -> None:
    cache_key = "korone-reboot"
    if await cache.get(cache_key):
        await cache.delete(cache_key)

    message = callback.message

    await message.edit_reply_markup()
    sent = await message.reply("Upgrading...")

    commands = [
        "git reset --hard origin/main",
        "pybabel compile -d locales -D bot",
        "rye sync --update-all --all-features",
    ]

    try:
        stdout = "".join([await run_command(command) for command in commands])
    except Exception as e:
        await sent.edit(f"An error occurred:\n<code>{e}</code>")
        return

    text = "Upgrade completed successfully. Reboot is required..."
    if len(stdout) > 4096:
        await sent.edit(text)
        await generate_document(stdout, message)
        return

    await sent.edit(f"<pre language='bash'>{html.escape(str(stdout))}</pre>")
