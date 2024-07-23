# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
import os
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

from hydrogram import Client
from hydrogram.filters import AndFilter, Filter

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Documents
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.utils.logging import logger
from korone.utils.traverse import bfs_attr_search

MODULES: dict[str, dict[str, Any]] = {}
COMMANDS: dict[str, Any] = {}


def add_handlers(module_name: str, handlers_path: Path) -> None:
    MODULES[module_name]["handlers"] = [
        f"{module_name}.handlers.{file.stem}"
        for file in handlers_path.glob("*.py")
        if file.name != "__init__.py"
    ]
    logger.debug("Handlers added for module %s: %s", module_name, MODULES[module_name]["handlers"])


def discover_modules() -> None:
    parent_path = Path(__file__).parent
    logger.debug("Discovering modules...")

    for entry in os.scandir(parent_path):
        if not entry.is_dir():
            continue

        if "handlers" not in os.listdir(entry.path):
            continue

        module_name = entry.name
        MODULES[module_name] = {"handlers": []}

        logger.debug("Discovered module: %s", module_name)
        add_handlers(module_name, Path(entry.path) / "handlers")


def get_method_callable(cls: type, key: str) -> Callable[..., Any]:
    method = cls.__dict__.get(key)

    if isinstance(method, staticmethod):
        logger.debug("Found static method: %s in %s", key, cls.__name__)
        return method.__func__

    method = bfs_attr_search(cls, key)

    if inspect.iscoroutinefunction(method):
        logger.debug("Found coroutine method: %s in %s", key, cls.__name__)
        return lambda *args, **kwargs: method(cls(), *args, **kwargs)

    logger.debug("Found method: %s in %s", key, cls.__name__)
    return lambda *args, **kwargs: method(cls(), *args, **kwargs)


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
    filtered_commands = [cmd.replace("$", "") for cmd in commands if cmd is not None]

    if not filtered_commands:
        await logger.adebug("No commands to update.")
        return

    parent, *children = filtered_commands
    COMMANDS[parent] = {"chat": {}, "children": children}

    for cmd in children:
        COMMANDS[cmd] = {"parent": parent}

    await logger.adebug("Command structure updated for parent: %s, children: %s", parent, children)

    command_state = await fetch_command_state(parent)
    if not command_state:
        return

    for each in command_state:
        COMMANDS[parent]["chat"][each["chat_id"]] = bool(each["state"])

    await logger.adebug("Command state integrated into command structure for %s", parent)


async def process_filters(filters: Filter) -> None:
    commands, disableable = [], False

    if hasattr(filters, "commands"):
        disableable, commands = await extract_commands_info(filters)
    elif (
        isinstance(filters, AndFilter)
        and hasattr(filters, "base")
        and hasattr(filters.base, "commands")
    ):
        disableable, commands = await extract_commands_info(filters.base)
    elif hasattr(filters, "patterns"):
        disableable, commands = await extract_patterns_info(filters)
    elif hasattr(filters, "base") and hasattr(filters.base, "patterns"):  # type: ignore
        disableable, commands = await extract_patterns_info(filters.base)  # type: ignore

    if not commands or not disableable:
        return

    await update_command_structure(commands)


async def extract_commands_info(filter_obj: Filter) -> tuple[bool, list[str]]:
    disableable = getattr(filter_obj, "disableable", False)
    commands = [cmd.pattern for cmd in getattr(filter_obj, "commands", [])]

    await logger.adebug("Commands extracted: %s, disableable: %s", commands, disableable)
    return disableable, commands


async def extract_patterns_info(filter_obj: Filter) -> tuple[bool, list[str]]:
    disableable = bool(getattr(filter_obj, "friendly_name", None))
    commands = [filter_obj.friendly_name] if getattr(filter_obj, "friendly_name", None) else []  # type: ignore

    await logger.adebug("Patterns extracted: %s", commands)
    return disableable, commands


async def register_handler(client: Client, module: ModuleType) -> bool:
    success = False
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if inspect.getmodule(obj) != module or not issubclass(
            obj, MessageHandler | CallbackQueryHandler
        ):
            continue

        for name, func in inspect.getmembers(obj):
            if not hasattr(func, "handlers"):
                continue

            method_callable = get_method_callable(obj, name)
            if handler := bfs_attr_search(func, "handlers"):
                client.add_handler(handler.event(method_callable, handler.filters), handler.group)
                await process_filters(handler.filters)
                await logger.adebug("Handler registered: %s for %s", name, module.__name__)
                success = True

    return success


async def load_module(client: Client, module_name: str, handlers: list[str]) -> bool:
    await logger.adebug("Loading module: %s", module_name)
    try:
        for handler in handlers:
            component = import_module(f".{handler}", "korone.modules")
            if not await register_handler(client, component):
                await logger.adebug("Failed to register handler for module: %s", module_name)
                return False
    except ModuleNotFoundError as err:
        msg = f"Could not load module: {module_name}"
        await logger.aerror(msg)
        raise ModuleNotFoundError(msg) from err

    await logger.adebug("Module loaded successfully: %s", module_name)
    return True


async def load_all_modules(client: Client) -> None:
    await logger.adebug("Loading all modules...")
    discover_modules()

    loaded_count = 0
    for module_name, module_info in MODULES.items():
        if not await load_module(client, module_name, module_info["handlers"]):
            continue
        loaded_count += 1

    await logger.ainfo("Loaded %s modules", loaded_count)
