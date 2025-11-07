from asyncio import gather
from importlib import import_module
from types import ModuleType
from typing import Sequence, Type, Union

from aiogram import Dispatcher, Router

from sophie_bot.modules.utils_.base_handler import SophieBaseHandler
from sophie_bot.utils.logger import log

LOADED_MODULES: dict[str, ModuleType] = {}
MODULES = [
    "op",
    "troubleshooters",  # troubleshooters always first!
    "error",
    "users",
    "notes",
    "help",
    "federations",
    "privacy",
    "disabling",
    "rules",
    "promotes",
    "greetings",  # After feds
    "welcomesecurity",
    "purges",
    "warns",
    "restrictions",
    "ai",
    "filters",
    # "antiflood",
    "legacy_modules",  # Legacy last
]


async def load_modules(
    dp: Union[Dispatcher, Router],
    to_load: Sequence[str],
    to_not_load: Sequence[str] = (),
):
    log.info("Importing modules...")
    if "*" in to_load:
        log.debug("Loading all modules...", modules=MODULES)
        to_load = MODULES
    else:
        log.info("Loading modules", to_load=to_load)

    for module_name in (x for x in MODULES if x in to_load and x not in to_not_load):
        path = f"sophie_bot.modules.{module_name}"

        module = import_module(path)

        if router := getattr(module, "router", None):
            dp.include_router(router)
        else:
            log.debug(f"! Module {module_name} has no router!")

        LOADED_MODULES[module.__name__.split(".", 3)[2]] = module

    for module_name, module in LOADED_MODULES.items():
        # Load handlers
        if not (router := getattr(module, "router", None)):
            continue

        handlers: Sequence[Type[SophieBaseHandler]] = getattr(module, "__handlers__", [])
        for handler in handlers:
            handler.register(router)

    # Pre setup
    await gather(
        *(func() for module_name, module in LOADED_MODULES.items() if (func := getattr(module, "__pre_setup__", None)))
    )

    # Post setup
    await gather(
        *(
            func(LOADED_MODULES)
            for module_name, module in LOADED_MODULES.items()
            if (func := getattr(module, "__post_setup__", None))
        )
    )

    log.info(f"Loaded modules - {', '.join(LOADED_MODULES.keys())}")
