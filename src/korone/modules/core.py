# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
import os
from collections.abc import Callable
from contextlib import suppress
from importlib import import_module
from pathlib import Path
from types import FunctionType, ModuleType
from typing import TYPE_CHECKING, Any

from hydrogram import Client
from hydrogram.filters import AndFilter
from magic_filter import MagicFilter

from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Documents
from korone.handlers import CallbackQueryHandler, MessageHandler
from korone.utils.logging import log
from korone.utils.traverse import bfs_attr_search

if TYPE_CHECKING:
    from korone.decorators.factory import HandlerObject

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

NOT_DISABLEABLE: list[str] = ["disableable", "enable", "disable"]


def add_module_info(module_name: str, module_info: Callable) -> None:
    """
    Add module information to the MODULES dictionary.

    This function adds information about a module to the MODULES dictionary.

    Parameters
    ----------
    module_name : str
        The name of the module.
    module_info : Callable
        The module information. This should be a callable object that provides
        information about the module, such as its name, summary, and documentation.

    Raises
    ------
    ValueError
        If any of the required attributes are missing in the module information.

    Notes
    -----
    The `module_info` parameter should be a callable object that returns a dictionary
    with the following attributes:

    - 'name' (str): The name of the module.
    - 'summary' (str): A brief summary of the module's functionality.
    - 'doc' (str): The documentation for the module.
    """
    MODULES[module_name] = {"handlers": [], "info": {}}

    for attr in ["name", "summary", "doc"]:
        attr_value = bfs_attr_search(module_info, attr)
        if attr_value is None:
            msg = f"Missing attribute '{attr}' in ModuleInfo of module '{module_name}'"
            raise ValueError(msg)
        MODULES[module_name]["info"][attr] = attr_value


def add_handlers(module_name: str, handlers_path: Path) -> None:
    """
    Add handlers to the MODULES dictionary.

    This function adds handlers to the MODULES dictionary. Each handler is represented as a string
    in the format "{module_name}.handlers.{handler_name}" and is appended to the list of handlers
    for the specified module in the MODULES dictionary.

    Parameters
    ----------
    module_name : str
        The name of the module.
    handlers_path : Path
        The path to the handlers directory.
    """
    for file in handlers_path.glob("*.py"):
        if file.name == "__init__.py":
            continue
        MODULES[module_name]["handlers"].append(f"{module_name}.handlers.{file.stem}")


def add_modules_to_dict() -> None:
    """
    Add modules to the MODULES dictionary.

    This function searches for modules in the `korone.modules` package and adds them to the MODULES
    dictionary. It looks for modules in the `handlers` subdirectory of each module's directory.
    If a module has a `ModuleInfo` class defined, it adds the module information to the MODULES
    dictionary. It also adds the handlers found in the `handlers` subdirectory to the MODULES
    dictionary.

    Notes
    -----
    The MODULES dictionary is a global dictionary used to store information about the modules and
    their handlers.
    """
    parent_path = Path(__file__).parent

    for root, dirs, _files in os.walk(parent_path):
        if "handlers" not in dirs:
            continue

        handlers_path = Path(root) / "handlers"
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


def get_method_callable(cls: type, key: str) -> Callable[..., Any]:
    """
    Get a callable method from a class.

    This function checks if the method is a static method or an asynchronous method.
    If it is a static method, it returns the method itself.
    If it is an asynchronous method, it returns an async function that calls the method.
    Otherwise, it returns a regular function that calls the method.

    Parameters
    ----------
    key : str
        The name of the method to retrieve.

    Returns
    -------
    collections.abc.Callable[..., typing.Any]
        The callable method.

    Examples
    --------
    >>> class MyClass:
    ...     def my_method(self):
    ...         return "Hello, world!"
    >>> my_instance = MyClass()
    >>> get_method_callable(MyClass, "my_method")(my_instance)
    'Hello, world!'
    """
    if isinstance(cls.__dict__.get(key), staticmethod):
        return cls.__dict__[key].__func__

    method = bfs_attr_search(cls, key)
    is_async = inspect.iscoroutinefunction(method)

    if is_async:

        async def async_call(*args, **kwargs):
            return await method(cls(), *args, **kwargs)

        return async_call

    def call(*args, **kwargs):
        return method(cls(), *args, **kwargs)

    return call


async def check_command_state(command: str) -> Documents | None:
    """
    Check the state of a command.

    This function checks the state of a command in the database and returns the command state.

    Parameters
    ----------
    command : str
        The command to check.

    Returns
    -------
    Documents | None
        The command state if it exists, None otherwise.
    """
    async with SQLite3Connection() as conn:
        table = await conn.table("Commands")
        query = Query()

        doc = await table.query(query.command == command)
        return doc or None


def update_commands(commands: list[str], parent: str, command_state: Documents | None) -> None:
    """
    Update the COMMANDS dictionary with the specified commands.

    This function updates the COMMANDS dictionary with the specified commands. It adds the parent
    command and its children to the dictionary, along with their chat state.

    If the command state is not provided, the function initializes the chat state for the parent
    command as an empty dictionary. If the command state is provided, the function updates the
    chat state for the parent command with the provided state.

    Parameters
    ----------
    commands : list[str]
        The list of commands to update.
    parent : str
        The parent command.
    command_state : Documents | None
        The command state for the parent command.
    """
    children = [command.replace("$", "") for command in commands[1:]]
    COMMANDS[parent] = {
        "chat": {},
        "children": children,
    }

    for cmd in children:
        COMMANDS[cmd] = {
            "parent": parent,
        }

    if not command_state:
        COMMANDS[parent]["chat"] = {}
    else:
        for each in command_state:
            COMMANDS[parent]["chat"][each["chat_id"]] = bool(each["state"])


async def register_handler(client: Client, module: ModuleType) -> bool:
    """
    Register handlers for a module in the client.

    This function searches for classes in the module that are subclasses of
    MessageHandler or CallbackQueryHandler, and that have methods that are
    instances of FunctionType. It adds these methods as handlers in the client.

    If a handler has associated commands, the function checks and updates the
    state of these commands.

    Parameters
    ----------
    client : hydrogram.Client
        The client object to register the handler with.
    module : types.ModuleType
        The module containing the handler functions.

    Returns
    -------
    bool
        True if at least one handler was successfully registered, False otherwise.
    """
    function_list = [
        (obj, func_obj)
        for _, obj in inspect.getmembers(module)
        if inspect.isclass(obj)
        and inspect.getmodule(obj) == module
        and (issubclass(obj, MessageHandler) or issubclass(obj, CallbackQueryHandler))
        for _, func_obj in inspect.getmembers(obj)
        if isinstance(func_obj, FunctionType)
    ]

    success = False

    for cls, func in function_list:
        if not hasattr(cls, func.__name__):
            continue

        method = bfs_attr_search(cls, func.__name__)
        if not callable(method):
            continue

        if not hasattr(method, "handlers"):
            continue

        method_callable = get_method_callable(cls, func.__name__)

        handler: HandlerObject = bfs_attr_search(method, "handlers")
        filters = handler.filters
        group = handler.group

        client.add_handler(handler.event(method_callable, filters), group)

        commands = []
        if hasattr(filters, "commands") and not isinstance(filters, MagicFilter):
            commands += [command.pattern for command in filters.commands]  # type: ignore

        elif isinstance(filters, AndFilter) and hasattr(filters.base, "commands"):
            commands += [command.pattern for command in filters.base.commands]

        if commands:
            parent = commands[0].replace("$", "")
            if parent not in NOT_DISABLEABLE:
                command_state = await check_command_state(parent)
                update_commands(commands, parent, command_state)

        log.debug("Handler registered", handler=handler)

        success = True

    return success


async def load_module(client: Client, module: tuple) -> bool:
    """
    Load specified module.

    This function loads a module into the Hydrogram's Client.

    Parameters
    ----------
    client : hydrogram.Client
        The Hydrogram's Client instance.
    module : tuple
        The module to be loaded.

    Returns
    -------
    bool
        True if the module was loaded successfully, False otherwise.

    Raises
    ------
    TypeError
        If the client has not been initialized.

    ModuleNotFoundError
        If the module cannot be found.
    """
    module_name: str = module[0]

    try:
        log.debug("Loading module: %s", module_name)

        for handler in module[1]["handlers"]:
            pkg: str = handler
            modules_path: str = "korone.modules"

            component: ModuleType = import_module(f".{pkg}", modules_path)
            if not await register_handler(client, component):
                return False

    except ModuleNotFoundError as err:
        msg = f"Could not load module: {module_name}"
        raise ModuleNotFoundError(msg) from err

    return True


async def load_all_modules(client: Client) -> None:
    """
    Load all modules.

    This function loads all modules from the `korone.modules` package.

    Parameters
    ----------
    client : hydrogram.Client
        The client object.
    """
    count: int = 0

    add_modules_to_dict()

    for module in MODULES.items():
        module_name = module[0]
        try:
            await load_module(client, module)
            count += 1
        except (TypeError, ModuleNotFoundError):
            log.exception("Could not load module: %s", module_name)

    log.info("Loaded %d modules", count)
