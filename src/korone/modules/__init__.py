from importlib import import_module
from inspect import iscoroutinefunction
from typing import TYPE_CHECKING

from anyio import create_task_group
from anyio.to_thread import run_sync

from korone.logging import get_logger as get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import ModuleType

    from aiogram import Dispatcher, Router

    from korone.utils.handlers import KoroneBaseHandler

logger = get_logger(__name__)

LOADED_MODULES: dict[str, ModuleType] = {}
MODULES = ["troubleshooters", "op", "error", "users", "help", "privacy", "disabling", "language"]


async def load_modules(dp: Dispatcher | Router, to_load: Sequence[str], to_not_load: Sequence[str] = ()) -> None:
    await logger.ainfo("Importing modules...")
    if "*" in to_load:
        await logger.adebug("Loading all modules...", modules=MODULES)
        to_load = MODULES
    else:
        await logger.ainfo("Loading modules", to_load=to_load)

    for module_name in (x for x in MODULES if x in to_load and x not in to_not_load):
        path = f"korone.modules.{module_name}"

        module = import_module(path)

        if router := getattr(module, "router", None):
            dp.include_router(router)
        else:
            await logger.adebug(f"! Module {module_name} has no router!")

        LOADED_MODULES[module.__name__.split(".", 3)[2]] = module

    for module_name, module in LOADED_MODULES.items():
        await logger.adebug(f"Loading module {module_name}...")
        if not (router := getattr(module, "router", None)):
            continue

        handlers: Sequence[type[KoroneBaseHandler]] = getattr(module, "__handlers__", [])
        for handler in handlers:
            await logger.adebug(f"Registering handler {handler.__name__}...")
            handler.register(router)

    async with create_task_group() as tg:
        for module_name, module in LOADED_MODULES.items():
            if func := getattr(module, "__pre_setup__", None):
                if iscoroutinefunction(func):
                    tg.start_soon(func)
                else:
                    tg.start_soon(run_sync, func)

    async with create_task_group() as tg:
        for module_name, module in LOADED_MODULES.items():
            if func := getattr(module, "__post_setup__", None):
                if iscoroutinefunction(func):
                    tg.start_soon(func, LOADED_MODULES)
                else:
                    tg.start_soon(run_sync, func, LOADED_MODULES)

    await logger.ainfo(f"Loaded modules - {', '.join(LOADED_MODULES.keys())}")
