# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import inspect
from importlib import import_module
from typing import TYPE_CHECKING, Any

from anyio import Path
from hydrogram.handlers.handler import Handler

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.utils.logging import get_logger

if TYPE_CHECKING:
    from types import ModuleType

    from hydrogram import Client
    from hydrogram.filters import Filter

    from korone.database.table import Documents

logger = get_logger(__name__)

MODULES: dict[str, dict[str, list[str]]] = {}
COMMANDS: dict[str, dict[str, Any]] = {}


async def discover_modules() -> None:
    """
    Discovers all available modules by scanning the module directory.

    This function looks for directories that contain a 'handlers' subdirectory
    and registers them as modules along with their handler files.
    """
    parent_path = Path(__file__).parent
    logger.debug("Discovering modules...")

    async for entry in parent_path.iterdir():
        if not await entry.is_dir():
            continue

        handlers_path = entry / "handlers"
        if not await handlers_path.exists():
            continue

        module_name = entry.name

        handlers: list[str] = []
        async for file in handlers_path.glob("*.py"):
            if file.name == "__init__.py":
                continue
            handlers.append(f"{module_name}.handlers.{file.stem}")

        if handlers:
            MODULES[module_name] = {"handlers": handlers}
            logger.debug("Discovered module: %s", module_name)


async def fetch_command_state(command: str) -> Documents | None:
    """
    Fetches the current state of a command from the database.

    Args:
        command: The command identifier to fetch the state for.

    Returns:
        Documents object containing the command state or None if not found.
    """
    await logger.adebug("Fetching command state for: %s", command)

    if command in COMMANDS and "parent" in COMMANDS[command]:
        command = COMMANDS[command]["parent"]

    async with SQLite3Connection() as conn:
        table = await conn.table("Commands")
        result = await table.query(Query().command == command) or None

        await logger.adebug("Command state fetched for %s: %s", command, result)
        return result


def extract_commands(filters: Filter) -> list[str | None] | None:
    """
    Extracts command patterns from filter objects.

    Args:
        filters: The filter object to extract commands from.

    Returns:
        A list of command patterns or None if no commands found.
    """
    # Import here to avoid circular import
    from korone.filters import Command, Regex  # noqa: PLC0415

    try:
        if isinstance(filters, Command) and filters.disableable:
            return [cmd.pattern for cmd in filters.command_patterns]
        if isinstance(filters, Regex):
            return [filters.friendly_name]
    except AttributeError:
        pass
    return None


async def update_command_structure(commands: list[str | None]) -> None:
    """
    Updates the command structure with parent-child relationships and chat states.

    Args:
        commands: List of commands to process and structure.
    """
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
    """
    Processes filter objects to extract and update command structures.

    Args:
        filters: The filter object to process.
    """
    if commands := extract_commands(filters):
        await update_command_structure(commands)


async def load_module(client: Client, module_name: str, handlers: list[str]) -> bool:
    """
    Loads a specific module with its handlers into the client.

    Args:
        client: The Hydrogram client instance.
        module_name: Name of the module to load.
        handlers: List of handler paths to import.

    Returns:
        Boolean indicating whether the module was loaded successfully.
    """
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
    """
    Discovers and loads all available modules.

    This function initializes the module discovery process and then
    loads each discovered module into the provided client instance.

    Args:
        client: The Hydrogram client instance.
    """
    await logger.adebug("Loading all modules...")

    await discover_modules()

    loaded_count = 0
    for module_name, module_info in MODULES.items():
        if await load_module(client, module_name, module_info["handlers"]):
            loaded_count += 1

    await logger.ainfo("Loaded %d modules", loaded_count)
