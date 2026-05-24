import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import KW_ONLY, dataclass, field
from enum import StrEnum
from inspect import isawaitable, iscoroutinefunction
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from types import ModuleType

    from aiogram import Dispatcher, Router
    from babel.support import LazyProxy
    from stfu_tg import Doc

type MaybeAwaitable[T] = T | Awaitable[T]
type ModuleText = str | LazyProxy
type ModuleContent = ModuleText | Doc
type ModuleExportProvider = Callable[[int], MaybeAwaitable[object]]
type ModuleHandler = Any
type ModuleHook = Callable[..., object]
type ModuleStatsProvider = Callable[[], MaybeAwaitable[Doc]]


class ModuleScript(StrEnum):
    PRE_SETUP = "pre_setup"
    POST_SETUP = "post_setup"


@dataclass(frozen=True, slots=True)
class ModulePackage:
    name: ModuleText
    _: KW_ONLY
    icon: str = "?"
    summary: ModuleText = ""
    description: ModuleContent = ""
    public: bool = True


@dataclass(frozen=True, slots=True)
class ModuleExport:
    provider: ModuleExportProvider
    _: KW_ONLY
    private_only: bool = False

    async def collect(self, chat_id: int) -> object:
        result = self.provider(chat_id)
        if isawaitable(result):
            return await cast("Awaitable[object]", result)
        return result


@dataclass(frozen=True, slots=True)
class ModuleScripts:
    pre_setup: ModuleHook | None = None
    post_setup: ModuleHook | None = None

    def get(self, script: ModuleScript) -> ModuleHook | None:
        match script:
            case ModuleScript.PRE_SETUP:
                return self.pre_setup
            case ModuleScript.POST_SETUP:
                return self.post_setup
        return None


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    package: ModulePackage
    _: KW_ONLY
    router: Router | None = None
    handlers: tuple[ModuleHandler, ...] = ()
    scripts: ModuleScripts = field(default_factory=ModuleScripts)
    stats: ModuleStatsProvider | None = None
    export: ModuleExport | None = None


@dataclass(frozen=True, slots=True)
class LoadedModule:
    slug: str
    module: ModuleType
    manifest: ModuleManifest

    @classmethod
    def from_module(cls, slug: str, module: ModuleType) -> LoadedModule:
        manifest = getattr(module, "manifest", None)
        if not isinstance(manifest, ModuleManifest):
            msg = f"korone.modules.{slug} must expose a ModuleManifest named 'manifest'"
            raise TypeError(msg)
        return cls(slug=slug, module=module, manifest=manifest)

    @property
    def import_path(self) -> str:
        return self.module.__name__

    @property
    def router(self) -> Router | None:
        return self.manifest.router

    @property
    def handlers(self) -> tuple[ModuleHandler, ...]:
        return self.manifest.handlers

    @property
    def package(self) -> ModulePackage:
        return self.manifest.package

    @property
    def export_private_only(self) -> bool:
        return bool(self.manifest.export and self.manifest.export.private_only)

    def include_router(self, target: Dispatcher | Router) -> bool:
        if self.router is None:
            return False

        target.include_router(self.router)
        return True

    def register_handlers(self) -> tuple[str, ...]:
        if self.router is None:
            return ()

        for handler in self.handlers:
            handler.register(self.router)
        return tuple(handler.__name__ for handler in self.handlers)

    def has_script(self, script: ModuleScript) -> bool:
        return self.manifest.scripts.get(script) is not None

    async def run_script(self, script: ModuleScript, *args: object) -> None:
        hook = self.manifest.scripts.get(script)
        if hook is None:
            return

        result: object
        if iscoroutinefunction(hook):
            result = hook(*args)
        else:
            result = await asyncio.to_thread(hook, *args)

        if isawaitable(result):
            await cast("Awaitable[object]", result)

    async def collect_stats(self) -> Doc | None:
        if self.manifest.stats is None:
            return None

        result = self.manifest.stats()
        if isawaitable(result):
            return await cast("Awaitable[Doc]", result)
        return result

    async def export_data(self, chat_id: int) -> object:
        if self.manifest.export is None:
            return None
        return await self.manifest.export.collect(chat_id)


type ModuleRegistry = Mapping[str, LoadedModule]
