from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage, ModuleRegistry, ModuleScripts
from korone.utils.i18n import LazyProxy as LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .callbacks import PrivacyMenuCallback as PrivacyMenuCallback
from .handlers.export import EXPORTABLE_MODULES, TriggerExport
from .handlers.privacy import PrivacyMenu

router = Router(name="info")


def post_setup(modules: ModuleRegistry) -> None:
    EXPORTABLE_MODULES.clear()
    for module in modules.values():
        if module.manifest.export is not None:
            EXPORTABLE_MODULES.append(module)


manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Privacy"),
        icon="🕵️‍♂️️",
        summary=l_("Privacy and data controls"),
        description=LazyProxy(
            lambda: Doc(
                l_("View the bot privacy policy and review how data is handled."),
                l_("Export your available data as a JSON file."),
            )
        ),
    ),
    router=router,
    handlers=(PrivacyMenu, TriggerExport),
    scripts=ModuleScripts(post_setup=post_setup),
)
