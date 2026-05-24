import asyncio
from importlib import import_module
from typing import TYPE_CHECKING

from korone.logger import get_logger
from korone.modules.metadata import LoadedModule, ModuleScript

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from aiogram import Dispatcher, Router

logger = get_logger(__name__)

MODULES: tuple[str, ...] = (
    "troubleshooters",
    "op",
    "error",
    "users",
    "help",
    "privacy",
    "disabling",
    "language",
    "medias",
    "stickers",
    "gsm_arena",
    "regex",
    "lastfm",
    "web",
)
_MODULES_SET = frozenset(MODULES)

LOADED_MODULES: dict[str, LoadedModule] = {}


def _resolve_modules_to_load(
    to_load: Sequence[str], to_not_load: Sequence[str]
) -> tuple[list[str], list[str], list[str]]:
    requested = set(MODULES) if "*" in to_load else set(to_load)
    ignored = set(to_not_load)

    selected = [module_name for module_name in MODULES if module_name in requested and module_name not in ignored]
    unknown_requested = sorted({name for name in to_load if name != "*" and name not in _MODULES_SET})
    unknown_ignored = sorted(name for name in ignored if name not in _MODULES_SET)
    return selected, unknown_requested, unknown_ignored


def _import_modules(module_names: Sequence[str]) -> dict[str, LoadedModule]:
    imported_modules: dict[str, LoadedModule] = {}

    for module_name in module_names:
        path = f"korone.modules.{module_name}"
        imported_modules[module_name] = LoadedModule.from_module(module_name, import_module(path))

    return imported_modules


async def _attach_routers(
    dp: Dispatcher | Router, module_names: Sequence[str], modules: Mapping[str, LoadedModule]
) -> None:
    for module_name in module_names:
        module = modules[module_name]
        if not module.include_router(dp):
            await logger.adebug("Module has no router", module=module_name)


async def _register_handlers(module_names: Sequence[str], modules: Mapping[str, LoadedModule]) -> None:
    for module_name in module_names:
        module = modules[module_name]
        if module.router is None or not module.handlers:
            continue

        registered = module.register_handlers()
        await logger.adebug("Registering module handlers", module=module_name, handlers=registered)


async def _run_module_hooks(
    module_names: Sequence[str],
    modules: Mapping[str, LoadedModule],
    script: ModuleScript,
    hook_args: tuple[object, ...] = (),
) -> None:
    async with asyncio.TaskGroup() as tg:
        for module_name in module_names:
            module = modules[module_name]
            if not module.has_script(script):
                continue

            await logger.adebug("Running module hook", module=module_name, hook=script.value)
            tg.create_task(module.run_script(script, *hook_args), name=f"{module_name}:{script.value}")


async def load_modules(dp: Dispatcher | Router, to_load: Sequence[str], to_not_load: Sequence[str] = ()) -> None:
    await logger.ainfo("Importing modules...")
    module_names, unknown_requested, unknown_ignored = _resolve_modules_to_load(to_load, to_not_load)

    if "*" in to_load:
        await logger.adebug("Loading all modules", modules=MODULES)
    else:
        await logger.ainfo("Loading modules", modules=module_names)

    if unknown_requested:
        await logger.awarning("Unknown modules in modules_load ignored", modules=unknown_requested)
    if unknown_ignored:
        await logger.awarning("Unknown modules in modules_not_load ignored", modules=unknown_ignored)

    if not module_names:
        LOADED_MODULES.clear()
        await logger.awarning("No modules selected to load")
        return

    imported_modules = _import_modules(module_names)

    LOADED_MODULES.clear()
    LOADED_MODULES.update(imported_modules)

    await _attach_routers(dp, module_names, LOADED_MODULES)
    await _register_handlers(module_names, LOADED_MODULES)
    await _run_module_hooks(module_names, LOADED_MODULES, ModuleScript.PRE_SETUP)
    await _run_module_hooks(module_names, LOADED_MODULES, ModuleScript.POST_SETUP, (LOADED_MODULES,))

    await logger.ainfo("Loaded modules", modules=list(LOADED_MODULES))
