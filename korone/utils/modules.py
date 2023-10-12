# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

from importlib import import_module
from pathlib import Path

from pyrogram import Client
from pyrogram.handlers.handler import Handler

from ..config import config
from .logger import log

HELPABLE: list[str] = []
ALL_MODULES: list[str] = []


def load_modules(bot: Client):
    modules_path = config.get_config("modules_path")

    count = 0
    for path in sorted(Path(modules_path.replace(".", "/")).rglob("*.py")):
        module_path = ".".join((*path.parent.parts, path.stem))
        module = import_module(module_path)
        if not str(path).endswith("__init__.py"):
            ALL_MODULES.append(module_path)
        if not str(path).endswith("__init__.py") and hasattr(module, "__help__"):
            HELPABLE.append(module_path.split(".")[-1])

        for name in vars(module):
            # noinspection PyBroadException
            try:
                for handler, group in getattr(module, name).handlers:
                    if isinstance(handler, Handler) and isinstance(group, int):
                        bot.add_handler(handler, group)

                        count += 1
            except BaseException:
                pass

    if count > 0:
        log.info(
            "[%s] Successfully loaded %s module%s from %s",
            bot.name,
            count,
            "s" if count > 1 else "",
            modules_path,
        )
    else:
        log.warning(
            "[%s] No module loaded from %s",
            bot.name,
            modules_path,
        )
