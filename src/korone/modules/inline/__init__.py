from aiogram import Router

from korone.modules.metadata import ModuleManifest, ModulePackage, ModuleRegistry, ModuleScripts

from .handlers import InlineQueryAggregatorHandler
from .middlewares import InlineQueryRegistryMiddleware
from .registry import InlineQueryRegistry

router = Router(name="inline")


def pre_setup() -> None:
    router.inline_query.middleware(InlineQueryRegistryMiddleware())


def post_setup(modules: ModuleRegistry) -> None:
    registry = InlineQueryRegistry.from_modules(modules)
    middleware = next(
        (item for item in router.inline_query.middleware if isinstance(item, InlineQueryRegistryMiddleware)), None
    )
    if middleware is None:
        msg = "Inline query registry middleware is unavailable"
        raise RuntimeError(msg)
    middleware.configure(registry)


manifest = ModuleManifest(
    package=ModulePackage(name="Inline", public=False),
    router=router,
    handlers=(InlineQueryAggregatorHandler,),
    scripts=ModuleScripts(pre_setup=pre_setup, post_setup=post_setup),
)
