from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.command import ExampleHandler

router = Router(name="example")

manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Example"),
        icon="?",
        summary=l_("Short example module summary"),
        description=LazyProxy(lambda: Doc(l_("Describe the example module for users."))),
    ),
    router=router,
    handlers=(ExampleHandler,),
)
