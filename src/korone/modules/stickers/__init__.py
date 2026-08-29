from aiogram import Router

from korone.modules.metadata import ModuleExport, ModuleManifest, ModulePackage, ModuleScripts
from korone.ui import column
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .export import export_stickers
from .handlers.delpack import StickerDeletePackHandler
from .handlers.delsticker import StickerDeleteStickerHandler
from .handlers.getsticker import StickerGetStickerHandler
from .handlers.mypacks import StickerMyPacksHandler
from .handlers.steal import StickerStealHandler
from .handlers.stealpack import StickerStealPackHandler
from .handlers.switch import StickerSwitchDefaultPackHandler
from .middlewares import StickerPackProcessingMiddleware
from .stats import stickers_stats
from .utils.processing import StickerPackProcessingManager

router = Router(name="stickers")
processing_manager = StickerPackProcessingManager()


def pre_setup() -> None:
    router.message.middleware(StickerPackProcessingMiddleware(processing_manager))
    router.startup.register(processing_manager.start)
    router.shutdown.register(processing_manager.shutdown)


manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Stickers"),
        icon="🧩",
        summary=l_("Personal sticker pack management"),
        description=LazyProxy(
            lambda: column(
                l_("Copy stickers and supported media into your own packs."),
                l_("Manage tracked packs, set a default pack, and remove stickers."),
            )
        ),
    ),
    router=router,
    handlers=(
        StickerStealHandler,
        StickerStealPackHandler,
        StickerGetStickerHandler,
        StickerDeleteStickerHandler,
        StickerDeletePackHandler,
        StickerSwitchDefaultPackHandler,
        StickerMyPacksHandler,
    ),
    scripts=ModuleScripts(pre_setup=pre_setup),
    stats=stickers_stats,
    export=ModuleExport(export_stickers, private_only=True),
)
