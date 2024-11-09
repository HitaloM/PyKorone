from importlib import import_module
from types import ModuleType
from typing import Sequence, Type, Union

from aiogram import Dispatcher, Router

from sophie_bot.modules.utils_.base_handler import SophieBaseHandler
from sophie_bot.utils.logger import log

LOADED_MODULES: dict[str, ModuleType] = {}
# troubleshooters always first, then legacy_modules!
MODULES = [
    "troubleshooters",
    "legacy_modules",
    "error",
    "users",
    "notes",
    "help",
    "feds",
    "privacy",
    "disabling",
    "rules",
    "promotes",
    "greetings",
    "welcomesecurity",
    "purges",
    "ai",
]


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

        if router := getattr(module, "router", None):
            dp.include_router(router)
        else:
            log.warning(f"Module {module_name} has no router!")

        LOADED_MODULES[module.__name__.split(".", 3)[2]] = module

    # Load handlers
    for module_name, module in LOADED_MODULES.items():
        if not (router := getattr(module, "router", None)):
            continue

        handlers: Sequence[Type[SophieBaseHandler]] = getattr(module, "__handlers__", [])
        for handler in handlers:
            handler.register(router)

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
