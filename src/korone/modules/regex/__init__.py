from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.sed import SedHandler

router = Router(name="regex")

manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Regex"),
        icon="🧪",
        summary=l_("Regex substitutions for replied messages"),
        description=LazyProxy(
            lambda: Doc(
                l_(
                    "Use sed-style syntax to edit replied text. Example: s/old/new/g; "
                    "escape slashes as \\/ and chain with ';'."
                )
            )
        ),
    ),
    router=router,
    handlers=(SedHandler,),
)
