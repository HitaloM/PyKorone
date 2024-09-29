from importlib import import_module
from types import ModuleType
from typing import Sequence, Union

from aiogram import Dispatcher, Router

from sophie_bot.utils.logger import log

LOADED_MODULES: dict[str, ModuleType] = {}
# troubleshooters always first, then legacy_modules!
MODULES = ["troubleshooters", "legacy_modules", "error", "beta", "users", "notes", "help", "feds", "privacy", "ai"]


def load_modules(
    dp: Union[Dispatcher, Router],
    to_load: Sequence[str],
    to_not_load: Sequence[str] = (),
):
    log.debug("Importing modules...")
    if "*" in to_load:
        log.debug("Loading all modules...")
        to_load = MODULES
    else:
        log.info("Loading modules", to_load=to_load)

    for module_name in (x for x in MODULES if x in to_load and x not in to_not_load):
        path = f"sophie_bot.modules.{module_name}"

        module = import_module(path)

        if hasattr(module, "router"):
            dp.include_router(getattr(module, "router"))
        else:
            log.warning(f"Module {module_name} has no router!")

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
