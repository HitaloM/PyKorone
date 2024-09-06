# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import inspect
import os
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

from hydrogram.handlers.handler import Handler

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.utils.logging import logger

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import ModuleType

    from hydrogram import Client
    from hydrogram.filters import Filter

    from korone.database.table import Documents

ModuleHandlers = list[str]
CommandChatState = dict[str, bool]
CommandStructure = dict[str, dict[str, CommandChatState | list[str] | str]]
HandlerDict = list[tuple[Handler, int]]

MODULES: dict[str, dict[str, ModuleHandlers]] = {}
COMMANDS: CommandStructure = {}


class CommandWithPattern(Protocol):
    pattern: str


class FiltersWithCommands(Protocol):
    commands: list[CommandWithPattern]
    disableable: bool


class FiltersWithFriendlyName(Protocol):
    friendly_name: str


class HandlerFun(Protocol):
    handlers: list[tuple[Handler, int]]


def discover_modules() -> None:
    parent_path = Path(__file__).parent
    logger.debug("Discovering modules...")

    for entry in os.scandir(parent_path):
        if entry.is_dir() and "handlers" in os.listdir(entry.path):
            module_name = entry.name

            handlers = [
                f"{module_name}.handlers.{file.stem}"
                for file in (Path(entry.path) / "handlers").glob("*.py")
                if file.name != "__init__.py"
            ]

            MODULES[module_name] = {"handlers": handlers}
            logger.debug("Discovered module: %s", module_name)


async def fetch_command_state(command: str) -> Documents | None:
    await logger.adebug("Fetching command state for: %s", command)

    async with SQLite3Connection() as conn:
        table = await conn.table("Commands")
        result = await table.query(Query().command == command) or None

        await logger.adebug("Command state fetched for %s: %s", command, result)
        return result


def extract_command_filters(filters: Filter) -> list[str] | None:
    if hasattr(filters, "commands") and getattr(filters, "disableable", False):
        filters_with_commands = cast(FiltersWithCommands, filters)
        return [cast(CommandWithPattern, cmd).pattern for cmd in filters_with_commands.commands]
    return None


def extract_pattern_filters(filters: Filter) -> list[str] | None:
    if hasattr(filters, "friendly_name"):
        filters_with_friendly_name = cast(FiltersWithFriendlyName, filters)
        return [filters_with_friendly_name.friendly_name]
    return None


def extract_commands(filters: Filter) -> list[str] | None:
    for extractor in [extract_command_filters, extract_pattern_filters]:
        commands = extractor(filters)
        if commands:
            return commands
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

            chat_state = cast(CommandChatState, COMMANDS[parent]["chat"])
            chat_state[chat_id] = state
            COMMANDS[parent]["chat"] = chat_state

    await logger.adebug("Command state integrated into command structure for %s", parent)


async def process_filters(filters: Filter) -> None:
    commands = extract_commands(filters)
    if commands:
        await update_command_structure(commands)


async def register_handler(client: Client, handlers: list[tuple[Handler, int]]) -> bool:
    for handler, group in handlers:
        if isinstance(handler, Handler):
            await logger.adebug("Registering handler: %s", handler)
            client.add_handler(handler, group)

            if handler.filters is not None:
                await process_filters(handler.filters)

            await logger.adebug("Handler registered successfully: %s", handler)

    return True


def get_module_handlers(component: ModuleType) -> Generator[list[tuple[Handler, int]], Any, Any]:
    for func in vars(component).values():
        if inspect.isfunction(func) and hasattr(func, "handlers"):
            func_with_handlers = cast(HandlerFun, func)
            yield func_with_handlers.handlers


async def load_module(client: Client, module_name: str, handlers: ModuleHandlers) -> bool:
    await logger.adebug("Loading module: %s", module_name)

    try:
        for handler in handlers:
            component: ModuleType = import_module(f".{handler}", "korone.modules")
            await logger.adebug("Imported component: %s", component)

            module_handlers = get_module_handlers(component)

            for handler_funcs in module_handlers:
                await logger.adebug("Registering handler: %s", handler_funcs)
                if not await register_handler(client, handler_funcs):
                    await logger.aerror("Failed to register handler: %s", handler_funcs)
                    continue

                await logger.adebug("Handler registered successfully: %s", handler_funcs)

    except ModuleNotFoundError:
        await logger.aerror("Could not load module: %s", module_name)
        raise

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
