# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
import os
from collections.abc import Callable
from contextlib import suppress
from importlib import import_module
from pathlib import Path
from types import FunctionType, ModuleType
from typing import Any

from hydrogram import Client
from hydrogram.filters import AndFilter, Filter

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Documents
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.utils.logging import log
from korone.utils.traverse import bfs_attr_search

MODULES: dict[str, dict[str, Any]] = {}
"""A dictionary that stores information about the modules.

Examples
--------
>>> MODULES = {
...     "dummy": {
...         "info": {
...             "name": "Dummy System",
...             "summary": "The Dummy System is a special system implemented into Dummy Plugs.",
...             "doc": "Entry Plugs are capsule-like tubes which acts as the cockpit for Evangelion pilots."
...         },
...         "handlers": [
...             "pm_menu.handlers.eva00"
...             "pm_menu.handlers.eva01",
...             "pm_menu.handlers.eva02",
...         ]
...     }
... }
"""  # noqa: E501

COMMANDS: dict[str, Any] = {}
"""
Korone's command structure.

Examples
--------
>>> COMMANDS = {
...     "evangelion": {
...         "chat": {
...             -100123456789: True,
...             -100987654321: False,
...         },
...         "children": [
...             "eva01",
...             "eva02",
...         ],
...     },
...     "eva01": {
...         "parent": "evangelion",
...     },
...     "eva02": {
...         "parent": "evangelion",
...     },
... }
"""

NOT_DISABLEABLE: set[str] = set()
"""
A list of commands that cannot be disabled.

:type: list[str]
"""


def add_module_info(module_name: str, module_info: Callable) -> None:
    """
    Add Module Information

    This function adds module information to the MODULES dictionary.

    Parameters
    ----------
    module_name : str
        The name of the module.
    module_info : Callable
        The function to get the module information.
    """
    module_data = {"handlers": [], "info": {}}
    for attr in ["name", "summary", "doc"]:
        attr_value = bfs_attr_search(module_info, attr)
        if attr_value is None:
            msg = f"Missing attribute '{attr}' in ModuleInfo of module '{module_name}'"
            raise ValueError(msg)
        module_data["info"][attr] = attr_value
    MODULES[module_name] = module_data


def add_handlers(module_name: str, handlers_path: Path) -> None:
    """
    Add Handlers

    This function adds handlers to the MODULES dictionary for a given module.

    Parameters
    ----------
    module_name : str
        The name of the module.
    handlers_path : Path
        The path to the handlers for the module.
    """
    MODULES[module_name]["handlers"] = [
        f"{module_name}.handlers.{file.stem}"
        for file in handlers_path.glob("*.py")
        if file.name != "__init__.py"
    ]


def add_modules_to_dict() -> None:
    """
    Add Modules to Dictionary

    This function adds all modules in the parent directory to the MODULES dictionary.
    """
    parent_path = Path(__file__).parent
    for entry in os.scandir(parent_path):
        if entry.is_dir() and "handlers" in os.listdir(entry.path):
            handlers_path = Path(entry.path) / "handlers"
            module_name = handlers_path.relative_to(parent_path).parts[0]
            MODULES[module_name] = {"handlers": []}

            module_pkg = f"korone.modules.{module_name}"
            module = import_module(".__init__", module_pkg)
            module_info = None
            with suppress(AttributeError):
                module_info = bfs_attr_search(module, "ModuleInfo")

            if module_info:
                add_module_info(module_name, module_info)

            add_handlers(module_name, handlers_path)


def get_method_callable(cls: type, key: str) -> Callable[..., Any]:  # numpydoc ignore=PR02
    """
    Get Method Callable

    This function gets a callable method from a class.

    Parameters
    ----------
    cls : type
        The class to get the method from.
    key : str
        The name of the method.

    Returns
    -------
    Callable[..., Any]
        The callable method.
    """
    method = cls.__dict__.get(key)
    if isinstance(method, staticmethod):
        return method.__func__

    method = bfs_attr_search(cls, key)
    if inspect.iscoroutinefunction(method):

        async def async_call(*args, **kwargs):
            return await method(cls(), *args, **kwargs)

        return async_call

    def call(*args, **kwargs):
        return method(cls(), *args, **kwargs)

    return call


async def check_command_state(command: str) -> Documents | None:
    """
    Check Command State

    This function checks the state of a command in the database.

    Parameters
    ----------
    command : str
        The command to check.

    Returns
    -------
    Documents | None
        The state of the command, or None if it doesn't exist.
    """
    async with SQLite3Connection() as conn:
        table = await conn.table("Commands")
        query = Query()
        return await table.query(query.command == command) or None


async def process_handler_commands(filters: Filter) -> None:
    """
    Process Handler Commands

    This function processes the commands for a handler.

    Parameters
    ----------
    filters : Filter
        The filters for the handler.
    """
    if hasattr(filters, "commands"):
        commands = [command.pattern for command in filters.commands]  # type: ignore
        if filters.disableable:  # type: ignore
            await update_commands(commands)
        else:
            NOT_DISABLEABLE.update(commands)
    elif (
        isinstance(filters, AndFilter)
        and hasattr(filters, "base")
        and hasattr(filters.base, "commands")
    ):
        base_commands = [command.pattern for command in filters.base.commands]  # type: ignore
        if filters.base.disableable:  # type: ignore
            await update_commands(base_commands)
        else:
            NOT_DISABLEABLE.update(base_commands)


async def update_commands(commands: list[str]) -> None:
    """
    Update Commands

    This function updates the COMMANDS dictionary with new commands.

    Parameters
    ----------
    commands : list[str]
        The commands to add.
    """
    parent = commands[0].replace("$", "")
    children = [command.replace("$", "") for command in commands[1:]]

    COMMANDS[parent] = {
        "chat": {},
        "children": children,
    }

    for cmd in children:
        COMMANDS[cmd] = {"parent": parent}

    command_state = await check_command_state(parent)

    if command_state:
        for each in command_state:
            log.debug(
                "Fetched chat state from the database: %s => %s",
                each["chat_id"],
                bool(each["state"]),
            )
            COMMANDS[parent]["chat"][each["chat_id"]] = bool(each["state"])

    log.debug("New command node for '%s'", parent, node=COMMANDS[parent])


async def register_handler(client: Client, module: ModuleType) -> bool:
    """
    Register Handler

    This function registers a handler with the client.

    Parameters
    ----------
    client : Client
        The client to register the handler with.
    module : ModuleType
        The module to register.

    Returns
    -------
    bool
        True if the handler was successfully registered, False otherwise.
    """
    success = False
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if inspect.getmodule(obj) != module or not issubclass(
            obj, MessageHandler | CallbackQueryHandler
        ):
            continue

        for name, func in inspect.getmembers(obj, predicate=lambda x: isinstance(x, FunctionType)):
            if not hasattr(obj, name) or not callable(func):
                continue

            if not hasattr(func, "handlers"):
                continue

            method_callable = get_method_callable(obj, name)
            if handler := bfs_attr_search(func, "handlers"):
                client.add_handler(handler.event(method_callable, handler.filters), handler.group)
                await process_handler_commands(handler.filters)
                success = True
    return success


async def load_module(client: Client, module: tuple) -> bool:
    """
    Load Module

    This function loads a module and registers its handlers.

    Parameters
    ----------
    client : Client
        The client to register the handlers with.
    module : tuple
        The module to load.

    Returns
    -------
    bool
        True if the module was successfully loaded, False otherwise.
    """
    module_name: str = module[0]
    try:
        log.debug("Loading module: %s", module_name)
        for handler in module[1]["handlers"]:
            component = import_module(f".{handler}", "korone.modules")
            if not await register_handler(client, component):
                return False
    except ModuleNotFoundError as err:
        msg = f"Could not load module: {module_name}"
        raise ModuleNotFoundError(msg) from err
    return True


async def load_all_modules(client: Client) -> None:
    """
    Load All Modules

    This function loads all modules and registers their handlers.

    Parameters
    ----------
    client : Client
        The client to register the handlers with.
    """
    add_modules_to_dict()
    count = 0
    for module in MODULES.items():
        try:
            if await load_module(client, module):
                count += 1
        except (TypeError, ModuleNotFoundError):
            log.exception("Could not load module: %s", module[0])
    log.info("Loaded %d modules", count)
