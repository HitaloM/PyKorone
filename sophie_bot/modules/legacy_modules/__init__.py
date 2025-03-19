import asyncio
from importlib import import_module

from sophie_bot.config import CONFIG
from sophie_bot.utils.logger import log

from ...services.bot import dp
from .modules import ALL_MODULES, LOADED_LEGACY_MODULES


async def before_srv_task():
    loop = asyncio.get_event_loop()
    for module in [m for m in LOADED_LEGACY_MODULES if hasattr(m, "__before_serving__")]:
        log.debug(f"Before serving: {module.__name__}")
        await module.__before_serving__(loop)


async def __pre_setup__():
    modules = CONFIG.modules_load if len(CONFIG.modules_load) > 0 and "*" not in CONFIG.modules_load else ALL_MODULES
    modules = [x for x in modules if x not in CONFIG.legacy_modules_not_load]

    from .utils.register import legacy_states_router

    log.info("Legacy modules", to_load=modules)

    for module_name in modules:
        imported_module = import_module(f"sophie_bot.modules.legacy_modules.modules.{module_name}")
        LOADED_LEGACY_MODULES.append(imported_module)
        legacy_states_router.include_router(imported_module.router)

    log.info("Legacy modules: Modules loaded!")

    await before_srv_task()

    log.debug("Legacy modules: Pre setup")

    dp.include_router(legacy_states_router)


async def __post_setup__(_):
    from sophie_bot.modules.help.utils.extract_info import (
        HELP_MODULES,
        gather_module_help,
    )

    from .utils.register import legacy_modules_router

    log.debug("Legacy modules: Post setup")
    dp.include_router(legacy_modules_router)

    for module in LOADED_LEGACY_MODULES:
        module_name = module.__name__.split(".")[-1]
        if module_help := await gather_module_help(module):
            HELP_MODULES[module_name] = module_help
