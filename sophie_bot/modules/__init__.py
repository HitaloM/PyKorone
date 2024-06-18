from importlib import import_module
from types import ModuleType
from typing import Dict, Sequence, Union

from aiogram import Dispatcher, Router

from sophie_bot.utils.logger import log

LOADED_MODULES: Dict[str, ModuleType] = {}
MODULES = ["error"]


def load_modules(dp: Union[Dispatcher, Router], to_load: Sequence[str], to_not_load: Sequence[str] = ()):
    log.debug("Importing modules...")
    if "*" in to_load:
        log.debug("Loading all modules...")
        to_load = MODULES
    else:
        log.debug("Loading {} modules...", " ,".join(to_load))

    for module_name in (x for x in MODULES if x in to_load and x not in to_not_load):
        path = f"sophie_bot.modules.{module_name}"

        module = import_module(path)
        dp.include_router(getattr(module, "router"))

        LOADED_MODULES[module.__name__.split(".", 3)[2]] = module

    # Pre setup
    for module_name, module in LOADED_MODULES.items():
        if hasattr(module, "__pre_setup__"):
            getattr(module, "__pre_setup__")()

    # Post setup
    for module_name, module in LOADED_MODULES.items():
        if hasattr(module, "__post_setup__"):
            log.debug("Running post setup...", module=module_name)
            getattr(module, "__post_setup__")(LOADED_MODULES)

    log.info(f"Loaded modules - {', '.join(LOADED_MODULES.keys())}")
