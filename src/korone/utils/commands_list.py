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


def create_bot_commands(locale: str, i18n: I18nNew) -> list[BotCommand]:
    _ = i18n.gettext
    return [
        BotCommand(command="start", description=_("Start the bot.", locale=locale)),
        BotCommand(command="help", description=_("Show help message.", locale=locale)),
        BotCommand(command="about", description=_("About the bot.", locale=locale)),
        BotCommand(command="privacy", description=_("Show privacy policy.", locale=locale)),
        BotCommand(command="language", description=_("Change the bot language.", locale=locale)),
    ]


async def set_ui_commands(client: Client, i18n: I18nNew):
    with suppress(FloodWait):
        await client.delete_bot_commands()
        tasks = []

        for locale in (*i18n.available_locales, i18n.default_locale):
            commands = create_bot_commands(locale, i18n)
            language_code = locale.split("_")[0].lower() if "_" in locale else locale

            tasks.extend((
                asyncio.create_task(
                    client.set_bot_commands(
                        commands,
                        scope=BotCommandScopeAllPrivateChats(),
                        language_code=language_code,
                    )
                ),
                asyncio.create_task(
                    client.set_bot_commands(
                        commands,
                        scope=BotCommandScopeAllGroupChats(),
                        language_code=language_code,
                    )
                ),
            ))

        await asyncio.gather(*tasks)
