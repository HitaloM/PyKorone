# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import inspect
import os
from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import FunctionType, ModuleType
from typing import Any

from hydrogram import Client
from hydrogram.handlers.message_handler import MessageHandler

from korone.utils.logging import log


@dataclass
class Module:
    name: str
    package: str


MODULES: list[Module] = []


for root, dirs, files in os.walk(Path(__file__).parent):
    for file in files:
        if file.endswith(".py") and not file.startswith("_"):
            module_path = Path(root) / file
            module_name = (
                module_path.relative_to(Path(__file__).parent)
                .as_posix()[:-3]
                .replace(os.path.sep, ".")
            )
            name = module_name.split(".")[0]
            MODULES.append(
                Module(
                    name=name,
                    package=module_name,
                )
            )


def get_method_callable(cls: type, key: str) -> Callable[..., Any]:
    method = getattr(cls, key)
    if isinstance(getattr(cls, key), staticmethod):
        return method

    is_async = inspect.iscoroutinefunction(method)

    def call(*args, **kwargs):
        return method(cls(), *args, **kwargs)

    async def async_call(*args, **kwargs):
        return await method(cls(), *args, **kwargs)

    return async_call if is_async else call


def register_handler(client: Client, component: ModuleType) -> bool:
    function_list = [
        (obj, func_obj)
        for _, obj in inspect.getmembers(component)
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


def load_module(client: Client, module: Module) -> None:
    if client is None:
        log.critical("Hydrogram's Client client has not been initialized!")
        log.critical("User attempted to load commands before init.")

        raise TypeError("client has not been initialized!")

    try:
        log.info("Loading module %s", module.name)

        name: str = module.package
        pkg: str = "korone.modules"

        component: ModuleType = import_module(f".{name}", pkg)

    except ModuleNotFoundError as err:
        log.error("Could not load module %s: %s", module.name, err)
        raise

    register_handler(client, component)


def load_all_modules(client: Client) -> None:
    for module in MODULES:
        load_module(client, module)
