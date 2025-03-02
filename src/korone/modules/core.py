# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import inspect
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any

from hydrogram.handlers.handler import Handler

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.utils.logging import logger

if TYPE_CHECKING:
    from types import ModuleType

    from hydrogram import Client
    from hydrogram.filters import Filter

    from korone.database.table import Documents

MODULES: dict[str, dict[str, list[str]]] = {}
COMMANDS: dict[str, dict[str, Any]] = {}


def discover_modules() -> None:
    parent_path = Path(__file__).parent
    logger.debug("Discovering modules...")

    for entry in parent_path.iterdir():
        if entry.is_dir() and (entry / "handlers").exists():
            module_name = entry.name

            handlers = [
                f"{module_name}.handlers.{file.stem}"
                for file in (entry / "handlers").glob("*.py")
                if file.name != "__init__.py"
            ]

            MODULES[module_name] = {"handlers": handlers}
            logger.debug("Discovered module: %s", module_name)


async def fetch_command_state(command: str) -> Documents | None:
    await logger.adebug("Fetching command state for: %s", command)

    if command in COMMANDS and "parent" in COMMANDS[command]:
        command = COMMANDS[command]["parent"]

    async with SQLite3Connection() as conn:
        table = await conn.table("Commands")
        result = await table.query(Query().command == command) or None

        await logger.adebug("Command state fetched for %s: %s", command, result)
        return result


def extract_commands(filters: Filter) -> list[str] | None:
    try:
        if hasattr(filters, "commands"):
            return [cmd.pattern for cmd in filters.commands if filters.disableable]  # type: ignore
        if hasattr(filters, "friendly_name"):
            return [filters.friendly_name]  # type: ignore
    except AttributeError:
        pass
    return None


async def update_command_structure(commands: list[str]) -> None:
    await logger.adebug("Updating command structure for commands: %s", commands)

    filtered_commands = [cmd.replace("$", "") for cmd in commands if cmd]
    if not filtered_commands:
        await logger.adebug("No commands to update.")
        return

    parent, *children = filtered_commands
    COMMANDS[parent] = {"chat": {}, "children": children}

    for cmd in children:
        COMMANDS[cmd] = {"parent": parent, "chat": {}}

    await logger.adebug("Command structure updated for parent: %s, children: %s", parent, children)

    command_state = await fetch_command_state(parent)
    if command_state:
        for each in command_state:
            chat_id = each["chat_id"]
            state = bool(each["state"])

            chat_state = COMMANDS[parent]["chat"]
            chat_state[chat_id] = state
            COMMANDS[parent]["chat"] = chat_state

    await logger.adebug("Command state integrated into command structure for %s", parent)


async def process_filters(filters: Filter) -> None:
    if commands := extract_commands(filters):
        await update_command_structure(commands)


async def load_module(client: Client, module_name: str, handlers: list[str]) -> bool:
    await logger.adebug("Loading module: %s", module_name)

    for handler in handlers:
        try:
            component: ModuleType = import_module(f".{handler}", "korone.modules")
            await logger.adebug("Imported component: %s", component)

            for func in vars(component).values():
                if not (inspect.isfunction(func) and hasattr(func, "handlers")):
                    continue

                for handler, group in func.handlers:  # type: ignore
                    if not isinstance(handler, Handler):
                        continue

                    client.add_handler(handler, group)
                    if handler.filters is not None:
                        await process_filters(handler.filters)
                    await logger.adebug("Handler registered successfully: %s", handler)

        except ModuleNotFoundError:
            await logger.aerror("Could not load module: %s", module_name)
            return False

    await logger.adebug("Module loaded successfully: %s", module_name)
    return True


async def load_all_modules(client: Client) -> None:
    await logger.adebug("Loading all modules...")

    discover_modules()

    loaded_count = 0
    for module_name, module_info in MODULES.items():
        if await load_module(client, module_name, module_info["handlers"]):
            loaded_count += 1

    await logger.ainfo("Loaded %d modules", loaded_count)
