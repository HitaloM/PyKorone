# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from contextlib import suppress

from hydrogram import Client
from hydrogram.errors import FloodWait
from hydrogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
)

from .i18n import I18nNew


async def set_ui_commands(client: Client, i18n: I18nNew):
    _ = i18n.gettext

    with suppress(FloodWait):
        await client.delete_bot_commands()
        tasks = []
        for locale in i18n.available_locales:
            commands = [
                BotCommand(
                    command="start",
                    description=_("Start the bot", locale=locale),
                ),
                BotCommand(
                    command="help",
                    description=_("Show help message", locale=locale),
                ),
                BotCommand(
                    command="about",
                    description=_("Show information about the bot", locale=locale),
                ),
                BotCommand(
                    command="privacy",
                    description=_("Show privacy policy", locale=locale),
                ),
                BotCommand(
                    command="language",
                    description=_("Change the bot language", locale=locale),
                ),
            ]

            language_code = locale.split("_")[0].lower() if "_" in locale else locale

            tasks.extend([
                client.set_bot_commands(
                    commands, scope=BotCommandScopeAllPrivateChats(), language_code=language_code
                ),
                client.set_bot_commands(
                    commands, scope=BotCommandScopeAllGroupChats(), language_code=language_code
                ),
            ])

        await asyncio.gather(*tasks)
