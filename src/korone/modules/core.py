# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
import os
from collections.abc import Iterable
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.handlers.handler import Handler

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Documents
from korone.utils.logging import logger

if TYPE_CHECKING:
    from types import ModuleType

MODULES: dict[str, dict[str, Any]] = {}
COMMANDS: dict[str, Any] = {}


def add_handlers_to_module(module_name: str, handlers_path: Path) -> None:
    handlers = [
        f"{module_name}.handlers.{file.stem}"
        for file in handlers_path.glob("*.py")
        if file.name != "__init__.py"
    ]
    MODULES[module_name]["handlers"] = handlers
    logger.debug("Handlers added for module %s: %s", module_name, handlers)


def discover_modules() -> None:
    parent_path = Path(__file__).parent
    logger.debug("Discovering modules...")

    for entry in os.scandir(parent_path):
        if entry.is_dir() and "handlers" in os.listdir(entry.path):
            module_name = entry.name
            MODULES[module_name] = {"handlers": []}
            logger.debug("Discovered module: %s", module_name)
            add_handlers_to_module(module_name, Path(entry.path) / "handlers")


async def fetch_command_state(command: str) -> Documents | None:
    await logger.adebug("Fetching command state for: %s", command)
    async with SQLite3Connection() as conn:
        table = await conn.table("Commands")
        query = Query()
        result = await table.query(query.command == command) or None
        await logger.adebug("Command state fetched for %s: %s", command, result)
        return result


async def update_command_structure(commands: list[str]) -> None:
    await logger.adebug("Updating command structure for commands: %s", commands)
    filtered_commands = [cmd.replace("$", "") for cmd in commands if cmd]
    if not filtered_commands:
        await logger.adebug("No commands to update.")
        return

    parent, *children = filtered_commands
    COMMANDS[parent] = {"chat": {}, "children": children}
    for cmd in children:
        COMMANDS[cmd] = {"parent": parent}

    await logger.adebug("Command structure updated for parent: %s, children: %s", parent, children)

    command_state = await fetch_command_state(parent)
    if command_state:
        for each in command_state:
            COMMANDS[parent]["chat"][each["chat_id"]] = bool(each["state"])

    await logger.adebug("Command state integrated into command structure for %s", parent)


async def process_filters(filters: Filter) -> None:
    commands = extract_commands(filters)
    if commands:
        await update_command_structure(commands)


def extract_commands(filters: Filter) -> list[str]:
    for extractor in [extract_command_filters, extract_pattern_filters]:
        commands = extractor(filters)
        if commands:
            return commands
    return []


def extract_command_filters(filters: Filter) -> list[str]:
    if hasattr(filters, "commands") and getattr(filters, "disableable", False):
        return [cmd.pattern for cmd in filters.commands]  # type: ignore
    return []


def extract_pattern_filters(filters: Filter) -> list[str]:
    if hasattr(filters, "friendly_name"):
        return [filters.friendly_name]  # type: ignore
    return []


class HandlerProtocol(Protocol):
    handlers: list[tuple[Handler, int]]


async def register_handler(client: Client, func: HandlerProtocol) -> bool:
    successful = False

    for handler, group in func.handlers:
        if isinstance(handler, Handler):
            await logger.adebug("Registering handler: %s", handler)

            successful = True
            client.add_handler(handler, group)

            if handler.filters is not None:
                await process_filters(handler.filters)

            await logger.adebug("Handler registered successfully: %s", handler)

    return successful


async def load_module(client: Client, module_name: str, handlers: list[str]) -> bool:
    await logger.adebug("Loading module: %s", module_name)
    try:
        for handler in handlers:
            component: ModuleType = import_module(f".{handler}", "korone.modules")
            await logger.adebug("Imported component: %s", component)

            module_handlers: Iterable[HandlerProtocol] = cast(
                Iterable[HandlerProtocol],
                (
                    func
                    for func in vars(component).values()
                    if inspect.isfunction(func) and hasattr(func, "handlers")
                ),
            )

            for handler_func in module_handlers:
                await logger.adebug("Registering handler: %s", handler_func)
                if not await register_handler(client, handler_func):
                    await logger.aerror("Failed to register handler: %s", handler_func)
                    continue

                await logger.adebug("Handler registered successfully: %s", handler_func)

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
