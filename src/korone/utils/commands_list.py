# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from anyio import create_task_group
from hydrogram.errors import FloodWait
from hydrogram.types import (
    BotCommand,
    BotCommandScope,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hydrogram import Client

    from .i18n import I18nNew


def create_bot_commands(locale: str, i18n: I18nNew) -> Sequence[BotCommand]:
    _ = i18n.gettext
    return [
        BotCommand(command="start", description=_("Start the bot.", locale=locale)),
        BotCommand(command="help", description=_("Show help message.", locale=locale)),
        BotCommand(command="about", description=_("About the bot.", locale=locale)),
        BotCommand(command="privacy", description=_("Show privacy policy.", locale=locale)),
        BotCommand(command="language", description=_("Change the bot language.", locale=locale)),
    ]


async def set_ui_commands(client: Client, i18n: I18nNew) -> None:
    with suppress(FloodWait):
        await client.delete_bot_commands()

        scopes: list[BotCommandScope] = [
            BotCommandScopeAllPrivateChats(),
            BotCommandScopeAllGroupChats(),
        ]

        async with create_task_group() as tg:
            for locale in (*i18n.available_locales, i18n.default_locale):
                language_code = locale.split("_")[0].lower() if "_" in locale else locale
                commands = list(create_bot_commands(locale, i18n))
                for scope in scopes:
                    tg.start_soon(client.set_bot_commands, commands, scope, language_code)
