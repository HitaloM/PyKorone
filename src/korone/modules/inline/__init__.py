from aiogram import Router

from korone.modules.metadata import ModuleManifest, ModulePackage, ModuleRegistry, ModuleScripts

from .handlers import InlineQueryAggregatorHandler
from .registry import configure_inline_query_providers

router = Router(name="inline")


def post_setup(modules: ModuleRegistry) -> None:
    configure_inline_query_providers(modules)


manifest = ModuleManifest(
    package=ModulePackage(name="Inline", public=False),
    router=router,
    handlers=(InlineQueryAggregatorHandler,),
    scripts=ModuleScripts(post_setup=post_setup),
)
