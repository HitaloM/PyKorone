# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import logging
from importlib import import_module
from pathlib import Path
from typing import List

from pyrogram import Client
from pyrogram.handlers.handler import Handler

from korone.config import config

logger = logging.getLogger(__name__)

HELPABLE: List[str] = []
ALL_MODULES: List[str] = []


def load_modules(client: Client):
    modules_path = config.get_config("modules_path")

    count = 0
    for path in sorted(Path(modules_path.replace(".", "/")).rglob("*.py")):
        module_path = ".".join(path.parent.parts + (path.stem,))
        module = import_module(module_path)
        if not str(path).endswith("__init__.py"):
            ALL_MODULES.append(module_path)
        if not str(path).endswith("__init__.py") and hasattr(module, "__help__"):
            HELPABLE.append(module_path.split(".")[-1])

        for name in vars(module).keys():
            # noinspection PyBroadException
            try:
                for handler, group in getattr(module, name).handlers:
                    if isinstance(handler, Handler) and isinstance(group, int):
                        client.add_handler(handler, group)

                        count += 1
            except BaseException:
                pass

    if count > 0:
        logger.info(
            "[%s] Successfully loaded %s module%s from %s",
            client.name,
            count,
            "s" if count > 1 else "",
            modules_path,
        )
    else:
        logger.warning(
            "[%s] No module loaded from %s",
            client.name,
            modules_path,
        )
