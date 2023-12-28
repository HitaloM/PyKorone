# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import inspect
import os
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import FunctionType, ModuleType

from hydrogram import Client
from hydrogram.handlers.handler import Handler

from korone.utils.logging import log


@dataclass
class Module:
    name: str
    description: str
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
                    description="",
                    package=module_name,
                )
            )


def register_command(client: Client, command: FunctionType) -> bool:
    if client is None:
        return False

    successful: bool = False

    for handler, group in command.handlers:  # type: ignore
        if isinstance(handler, Handler) and isinstance(group, int):
            log.info("Registering command %s", command)
            log.info("\thandler: %s", handler)
            log.info("\tgroup:   %d", group)

            successful = True

            client.add_handler(handler, group)

            log.debug("Checking for command filters.")
            if handler.filters is None:
                continue

    return successful


def load_module(client: Client, module: Module) -> None:
    if client is None:
        log.critical("Hydrogram's Client client has not been initialized!")
        log.critical("User attempted to load commands before init.")

        raise TypeError("client has not been initialized!")

    try:
        log.info("Loading module %s", module.name)

        name: str = module.name
        pkg: str = "korone.modules"

        component: ModuleType = import_module(f".{name}", pkg)

    except ModuleNotFoundError as err:
        log.error("Could not load module %s: %s", module.name, err)
        raise

    commands: Iterable[FunctionType] = []

    for var in vars(component):
        attr = getattr(component, var)

        if inspect.isclass(attr):
            for var_cls in vars(attr):
                attr_cls = getattr(attr, var_cls)
                if inspect.isfunction(attr_cls) and hasattr(attr_cls, "handlers"):
                    commands.append(attr_cls)
        elif inspect.isfunction(attr) and hasattr(attr, "handlers"):
            commands.append(attr)

    for command in commands:
        log.info("Adding command %s from module", command)
        if not register_command(client, command):
            log.info("Could not add command %s", command)
            continue

        log.info("Successfully added command %s", command)


def load_all_modules(client: Client) -> None:
    for module in MODULES:
        load_module(client, module)
