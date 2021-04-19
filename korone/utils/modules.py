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
import logging
import importlib
from types import ModuleType
from typing import List

modules: List[ModuleType] = []
log = logging.getLogger()


def load(bot):
    global modules

    files = glob.glob(f"korone/handlers/*.py", recursive=True)
    files = sorted(files, key=lambda file: file.split("/")[2])

    for file_name in files:
        try:
            module = importlib.import_module(
                file_name.replace("/", ".").replace(".py", "")
            )
            modules.append(module)
        except BaseException:
            log.error(f"Failed to import the module: {file_name}", exc_info=True)
            continue

        functions = [*filter(callable, module.__dict__.values())]
        functions = [*filter(lambda function: hasattr(function, "handlers"), functions)]

        for function in functions:
            for handler in function.handlers:
                bot.add_handler(*handler)

    log.info(
        f"{len(modules)} module{'s' if len(modules) != 1 else ''} imported successfully!"
    )


def reload(bot):
    global modules

    for index, module in enumerate(modules):
        functions = [*filter(callable, module.__dict__.values())]
        functions = [*filter(lambda function: hasattr(function, "handlers"), functions)]

        for function in functions:
            for handler in function.handlers:
                bot.remove_handler(*handler)

        module = importlib.reload(module)
        modules[index] = module

        functions = [*filter(callable, module.__dict__.values())]
        functions = [*filter(lambda function: hasattr(function, "handlers"), functions)]

        for function in functions:
            for handler in function.handlers:
                bot.add_handler(*handler)

    log.info(
        f"{len(modules)} module{'s' if len(modules) != 1 else ''} reloaded successfully!"
    )
