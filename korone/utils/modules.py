# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import glob
import importlib
import logging
from types import ModuleType
from typing import List

modules: List[ModuleType] = []
log = logging.getLogger()


def load(client):
    global modules

    files = glob.glob("korone/handlers/*.py")
    files = sorted(files, key=lambda file: file.split("/")[2])

    for file_name in files:
        try:
            module = importlib.import_module(
                file_name.replace("/", ".").replace(".py", "")
            )
            modules.append(module)
        except BaseException:
            log.error("Failed to import the module: %s", file_name, exc_info=True)
            continue

        functions = [*filter(callable, module.__dict__.values())]
        functions = [
            *filter(lambda function: hasattr(function, "handlers"), functions),
        ]

        for function in functions:
            for handler in function.handlers:
                client.add_handler(*handler)

    log.info(
        "%s imported successfully!",
        f"{len(modules)} module{'s' if len(modules) != 1 else ''}",
    )


def reload(client):
    global modules

    for index, module in enumerate(modules):
        functions = [*filter(callable, module.__dict__.values())]
        functions = [
            *filter(lambda function: hasattr(function, "handlers"), functions),
        ]

        for function in functions:
            for handler in function.handlers:
                client.remove_handler(*handler)

        module = importlib.reload(module)
        modules[index] = module

        functions = [*filter(callable, module.__dict__.values())]
        functions = [
            *filter(lambda function: hasattr(function, "handlers"), functions),
        ]

        for function in functions:
            for handler in function.handlers:
                client.add_handler(*handler)

    log.info(
        "%s reloaded successfully!",
        f"{len(modules)} module{'s' if len(modules) != 1 else ''}",
    )
