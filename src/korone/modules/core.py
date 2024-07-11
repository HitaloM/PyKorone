# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
import os
from collections.abc import Callable
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
COMMANDS: dict[str, Any] = {}
NOT_DISABLEABLE: set[str] = set()


def add_module_info(module_name: str, module_info: Callable) -> None:
    module_data = {"handlers": [], "info": {}}
    required_attrs = ["name", "summary", "doc"]
    for attr in required_attrs:
        attr_value = bfs_attr_search(module_info, attr)
        if attr_value is None:
            msg = f"Missing attribute '{attr}' in ModuleInfo of module '{module_name}'"
            raise ValueError(msg)
        module_data["info"][attr] = attr_value
    MODULES[module_name] = module_data


def add_handlers(module_name: str, handlers_path: Path) -> None:
    MODULES[module_name]["handlers"] = [
        f"{module_name}.handlers.{file.stem}"
        for file in handlers_path.glob("*.py")
        if file.name != "__init__.py"
    ]


def add_modules_to_dict() -> None:
    parent_path = Path(__file__).parent
    for entry in os.scandir(parent_path):
        if entry.is_dir() and "handlers" in os.listdir(entry.path):
            handlers_path = Path(entry.path) / "handlers"
            module_name = handlers_path.relative_to(parent_path).parts[0]
            MODULES[module_name] = {"handlers": []}

            module_pkg = f"korone.modules.{module_name}"
            try:
                module = import_module(".__init__", module_pkg)
                module_info = bfs_attr_search(module, "ModuleInfo")
                if module_info:
                    add_module_info(module_name, module_info)
            except AttributeError:
                pass

            add_handlers(module_name, handlers_path)


def get_method_callable(cls: type, key: str) -> Callable[..., Any]:  # numpydoc ignore=PR02
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
    async with SQLite3Connection() as conn:
        table = await conn.table("Commands")
        query = Query()
        return await table.query(query.command == command) or None


async def process_handler_commands(filters: Filter) -> None:
    async def update_commands_or_not_disableable(command_list: list, disableable: bool):
        if disableable:
            await update_commands(command_list)
        else:
            NOT_DISABLEABLE.update(command_list)

    if hasattr(filters, "commands"):
        commands = [command.pattern for command in filters.commands]  # type: ignore
        await update_commands_or_not_disableable(commands, filters.disableable)  # type: ignore
    elif (
        isinstance(filters, AndFilter)
        and hasattr(filters, "base")
        and hasattr(filters.base, "commands")
    ):
        base_commands = [command.pattern for command in filters.base.commands]  # type: ignore
        await update_commands_or_not_disableable(base_commands, filters.base.disableable)  # type: ignore


async def update_commands(commands: list[str]) -> None:
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
    success = False
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if inspect.getmodule(obj) != module or not issubclass(
            obj, MessageHandler | CallbackQueryHandler
        ):
            continue

        for name, func in inspect.getmembers(obj, predicate=lambda x: isinstance(x, FunctionType)):
            if not callable(func) or not hasattr(func, "handlers"):
                continue

            method_callable = get_method_callable(obj, name)
            if handler := bfs_attr_search(func, "handlers"):
                client.add_handler(handler.event(method_callable, handler.filters), handler.group)
                await process_handler_commands(handler.filters)
                success = True
    return success


async def load_module(client: Client, module: tuple) -> bool:
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
    add_modules_to_dict()
    count = 0
    for module in MODULES.items():
        try:
            if await load_module(client, module):
                count += 1
        except (TypeError, ModuleNotFoundError):
            log.exception("Could not load module: %s", module[0])
    log.info("Loaded %d modules", count)
