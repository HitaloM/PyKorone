from aiogram import Router

from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.ui import column
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.command import ExampleHandler

router = Router(name="example")

manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Example"),
        icon="?",
        summary=l_("Short example module summary"),
        description=LazyProxy(lambda: column(l_("Describe the example module for users."))),
    ),
    router=router,
    handlers=(ExampleHandler,),
)
