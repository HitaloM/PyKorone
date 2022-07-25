# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import logging
import os
from importlib import import_module
from pathlib import Path
from typing import List

from pyrogram import Client
from pyrogram.handlers.handler import Handler

logger = logging.getLogger(__name__)

ALL_MODULES: List[str] = []


def load_modules(client: Client):
    modules_path = client.korone_config["modules_path"]
    if not isinstance(modules_path, str):
        raise TypeError("Plugins path must be a string")

    try:
        exclude = client.korone_config["excluded_modules"]
        if not isinstance(exclude, list):
            raise TypeError("Excluded plugins must be a list of strings")
    except KeyError:
        exclude = False

    count = 0
    for path in sorted(Path(modules_path.replace(".", "/")).rglob("*.py")):
        if not str(path).endswith("__init__.py"):
            ALL_MODULES.append(os.path.basename(path))
        module_path = ".".join(path.parent.parts + (path.stem,))
        module = import_module(module_path)

        for name in vars(module).keys():
            # noinspection PyBroadException
            try:
                for handler, group in getattr(module, name).handlers:
                    if isinstance(handler, Handler) and isinstance(group, int):
                        client.add_handler(handler, group)

                        count += 1
            except BaseException:
                pass

    if exclude:
        for path, handlers in exclude:
            module_path = modules_path + "." + path
            warn_non_existent_functions = True

            try:
                module = import_module(module_path)
            except ImportError:
                logger.warning(
                    "[%s] [UNLOAD] Ignoring non-existent module %s",
                    client.name,
                    module_path,
                )
                continue

            if "__path__" in dir(module):
                logger.warning(
                    "[%s] [UNLOAD] Ignoring namespace %s",
                    client.name,
                    module_path,
                )
                continue

            if handlers is None:
                handlers = vars(module).keys()
                warn_non_existent_functions = False

            for name in handlers:
                # noinspection PyBroadException
                try:
                    for handler, group in getattr(module, name).handlers:
                        if isinstance(handler, Handler) and isinstance(group, int):
                            client.remove_handler(handler, group)

                            count -= 1
                except BaseException:
                    if warn_non_existent_functions:
                        logger.warning(
                            "[%s] [UNLOAD] Ignoring non-existent function %s from %s",
                            client.name,
                            name,
                            module_path,
                        )

    if count > 0:
        logger.info(
            "[%s] Successfully loaded %s plugin%s from %s",
            client.name,
            count,
            "s" if count > 1 else "",
            modules_path,
        )
    else:
        logger.warning(
            "[%s] No plugin loaded from %s",
            client.name,
            modules_path,
        )
