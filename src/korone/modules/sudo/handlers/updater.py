# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html

from hydrogram import Client
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from korone.constants import MESSAGE_LENGTH_LIMIT
from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.modules.sudo.callback_data import UpdateCallbackData
from korone.modules.sudo.utils import (
    fetch_updates,
    generate_changelog,
    generate_document,
    parse_commits,
    perform_update,
    restart_bot,
)


@router.message(Command(commands=["update", "upgrade"], disableable=False) & IsSudo)
async def update_command(client: Client, message: Message) -> None:
    sent = await message.reply("Checking for updates...")

    try:
        stdout = await fetch_updates()
    except Exception as e:
        await sent.edit(f"An error occurred:\n<code>{html.escape(str(e))}</code>")
        return

    if not stdout.strip():
        await sent.edit("There is nothing to update.")
        return

    commits = parse_commits(stdout)
    changelog = generate_changelog(commits)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Update", callback_data=UpdateCallbackData().pack())]
    ])
    await sent.edit(changelog, reply_markup=keyboard)


@router.callback_query(UpdateCallbackData.filter() & IsSudo)
async def update_callback(client: Client, callback: CallbackQuery) -> None:
    message = callback.message

    await callback.answer("Starting upgrade...")
    await message.edit_reply_markup()
    sent = await message.reply("Upgrading...")

    try:
        stdout = await perform_update()
    except Exception as e:
        await sent.edit(f"An error occurred:\n<code>{html.escape(str(e))}</code>")
        await callback.answer("Upgrade failed.", show_alert=True)
        return

    if len(stdout) > MESSAGE_LENGTH_LIMIT:
        await generate_document(stdout, message)
        final_text = "Upgrade completed successfully. Output sent as document. Rebooting..."
        await restart_bot(sent, final_text)
        return

    formatted_stdout = html.escape(stdout) if stdout else "No output returned."
    final_text = (
        "Upgrade completed successfully.\n"
        f"<pre language='bash'>{formatted_stdout}</pre>\n"
        "Rebooting..."
    )
    await restart_bot(sent, final_text)
