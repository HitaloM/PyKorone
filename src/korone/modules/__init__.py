from __future__ import annotations

import asyncio
from collections.abc import Callable
from importlib import import_module
from inspect import isawaitable, iscoroutinefunction
from typing import TYPE_CHECKING, cast

from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Mapping, Sequence
    from types import ModuleType

    from aiogram import Dispatcher, Router

    from korone.utils.handlers import KoroneBaseHandler

logger = get_logger(__name__)

type ModuleHook = Callable[..., object]

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
    "hifi",
    "regex",
    "lastfm",
    "web",
)
_MODULES_SET = frozenset(MODULES)

LOADED_MODULES: dict[str, ModuleType] = {}


def _resolve_modules_to_load(
    to_load: Sequence[str], to_not_load: Sequence[str]
) -> tuple[list[str], list[str], list[str]]:
    requested = set(MODULES) if "*" in to_load else set(to_load)
    ignored = set(to_not_load)

    selected = [module_name for module_name in MODULES if module_name in requested and module_name not in ignored]
    unknown_requested = sorted({name for name in to_load if name != "*" and name not in _MODULES_SET})
    unknown_ignored = sorted(name for name in ignored if name not in _MODULES_SET)
    return selected, unknown_requested, unknown_ignored


def _import_modules(module_names: Sequence[str]) -> dict[str, ModuleType]:
    imported_modules: dict[str, ModuleType] = {}

    for module_name in module_names:
        path = f"korone.modules.{module_name}"
        imported_modules[module_name] = import_module(path)

    return imported_modules


def _module_handlers(module: ModuleType) -> tuple[type[KoroneBaseHandler], ...]:
    handlers = tuple(getattr(module, "__handlers__", ()))
    return cast("tuple[type[KoroneBaseHandler], ...]", handlers)


async def _attach_routers(
    dp: Dispatcher | Router, module_names: Sequence[str], modules: Mapping[str, ModuleType]
) -> None:
    for module_name in module_names:
        module = modules[module_name]
        router = getattr(module, "router", None)
        if router is None:
            await logger.adebug("Module has no router", module=module_name)
            continue

        dp.include_router(router)


async def _register_handlers(module_names: Sequence[str], modules: Mapping[str, ModuleType]) -> None:
    for module_name in module_names:
        module = modules[module_name]
        router = getattr(module, "router", None)
        if router is None:
            continue

        handlers = _module_handlers(module)
        if not handlers:
            continue

        await logger.adebug("Registering module handlers", module=module_name, handlers=[h.__name__ for h in handlers])
        for handler in handlers:
            handler.register(router)


async def _run_hook(module_name: str, hook_name: str, hook: ModuleHook, hook_args: tuple[object, ...]) -> None:
    await logger.adebug("Running module hook", module=module_name, hook=hook_name)

    result: object
    if iscoroutinefunction(hook):
        result = hook(*hook_args)
    else:
        result = await asyncio.to_thread(hook, *hook_args)

    if isawaitable(result):
        await cast("Awaitable[object]", result)


async def _run_module_hooks(
    module_names: Sequence[str], modules: Mapping[str, ModuleType], hook_name: str, hook_args: tuple[object, ...] = ()
) -> None:
    async with asyncio.TaskGroup() as tg:
        for module_name in module_names:
            module = modules[module_name]
            hook = getattr(module, hook_name, None)
            if hook is None:
                continue
            if not callable(hook):
                await logger.awarning("Ignoring non-callable module hook", module=module_name, hook=hook_name)
                continue

            tg.create_task(
                _run_hook(module_name=module_name, hook_name=hook_name, hook=hook, hook_args=hook_args),
                name=f"{module_name}:{hook_name}",
            )


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
    await _run_module_hooks(module_names, LOADED_MODULES, "__pre_setup__")
    await _run_module_hooks(module_names, LOADED_MODULES, "__post_setup__", (LOADED_MODULES,))

    await logger.ainfo("Loaded modules", modules=list(LOADED_MODULES))
