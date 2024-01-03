# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import inspect
import os
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from types import FunctionType, ModuleType
from typing import Any

from hydrogram import Client
from hydrogram.handlers.message_handler import MessageHandler

from korone.utils.logging import log

MODULES: dict[str, dict[str, Any]] = {}
"""A dictionary that stores information about the modules.

Examples
--------
{
    "dummy": {
        "info": {
            "name": "Dummy System",
            "summary": "The Dummy System is a special system implemented into Dummy Plugs.",
            "doc": "Entry Plugs are capsule-like tubes which acts as the cockpit for Evangelion pilots."
        },
        "handlers": [
            "pm_menu.handlers.eva00"
            "pm_menu.handlers.eva01",
            "pm_menu.handlers.eva02",
        ]
    }
}
"""  # noqa: E501


def add_modules_to_dict() -> None:
    """
    Add modules to the MODULES dictionary.

    This function walks through the directory containing the modules and adds them to the MODULES
    dictionary. Each module is represented by a dictionary entry in the MODULES dictionary, with
    the module name as the key.
    """
    parent_path = Path(__file__).parent
    current_file_path = Path(__file__)

    for root, _, files in os.walk(parent_path):
        for file in files:
            if file.endswith(".py") and (not file.startswith("_") or file == "__init__.py"):
                module_path = Path(root) / file
                if module_path == current_file_path:
                    continue
                module_name = (
                    module_path.relative_to(parent_path).as_posix()[:-3].replace(os.path.sep, ".")
                )
                name = module_name.split(".")[0]
                if name not in MODULES:
                    MODULES[name] = {"info": {}, "handlers": []}

                if module_name.endswith("__init__"):
                    module = import_module(f"korone.modules.{name}")
                    module_info = getattr(module, "ModuleInfo", None)
                    if module_info:
                        for attr in ["name", "summary", "doc"]:
                            attr_value = getattr(module_info, attr, None)
                            if attr_value:
                                MODULES[name]["info"][attr] = attr_value
                    continue

                MODULES[name]["handlers"].append(module_name)


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
    Callable[..., Any]
        The callable method.

    Examples
    --------
    >>> class MyClass:
    ...     def my_method(self):
    ...         return "Hello, world!"
    ...
    >>> get_method_callable(MyClass, "my_method")()
    'Hello, world!'
    """

    method = getattr(cls, key)
    if isinstance(getattr(cls, key), staticmethod):
        return method

    is_async = inspect.iscoroutinefunction(method)

    def call(*args, **kwargs):
        return method(cls(), *args, **kwargs)

    async def async_call(*args, **kwargs):
        return await method(cls(), *args, **kwargs)

    return async_call if is_async else call


def register_handler(client: Client, module: ModuleType) -> bool:
    """
    Register a handler for a module in the client.

    This function registers a handler for a module in the client.

    Parameters
    ----------
    client : Client
        The client object to register the handler with.
    module : ModuleType
        The module containing the handler functions.

    Returns
    -------
    bool
        True if the registration was successful, False otherwise.
    """

    function_list = [
        (obj, func_obj)
        for _, obj in inspect.getmembers(module)
        if inspect.isclass(obj)
        for _, func_obj in inspect.getmembers(obj)
        if isinstance(func_obj, FunctionType)
    ]

    successful: bool = False

    for cls, func in function_list:
        method = getattr(cls, func.__name__)
        if not callable(method):
            continue

        if hasattr(method, "on"):
            method_callable = get_method_callable(cls, func.__name__)
            filters = getattr(method, "filters")
            group = getattr(method, "group", 0)

            if method.on == "message":
                client.add_handler(MessageHandler(method_callable, filters), group)  # type: ignore

            log.info("Registrando comando %s", filters.commands)
            log.info("\thandler: %s", cls.__name__)
            log.info("\tgroup:   %d", group)

            successful = True

    return successful


def load_module(client: Client, module: tuple) -> bool:
    """
    Load specified module.

    This function loads a module into the Hydrogram's Client.

    Parameters
    ----------
    client : Client
        The Hydrogram's Client instance.
    module : Module
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

    if client is None:
        log.critical("Hydrogram's Client client has not been initialized!")
        log.critical("User attempted to load commands before init.")

        raise TypeError("client has not been initialized!")

    module_name: str = module[0]

    try:
        log.info("Loading module: %s", module_name)

        for handler in module[1]["handlers"]:
            pkg: str = handler
            modules_path: str = "korone.modules"

            component: ModuleType = import_module(f".{pkg}", modules_path)
            if not register_handler(client, component):
                return False

        return True

    except ModuleNotFoundError:
        log.exception("Could not load module: %s", module_name)
        raise


def load_all_modules(client: Client) -> None:
    """
    Load all modules.

    This function loads all modules from the `korone.modules` package.

    Parameters
    ----------
    client : Client
        The client object.
    """

    modules: list = []

    add_modules_to_dict()

    for module in MODULES.items():
        module_name = module[0]
        try:
            load_module(client, module)
            modules.append(module_name)
        except BaseException:
            log.exception("Could not load module: %s", module_name)

    log.info("Loaded %d modules", len(modules))
