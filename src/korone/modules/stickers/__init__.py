from aiogram import Router
from stfu_tg import Doc

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
from .stats import stickers_stats

router = Router(name="stickers")

__module_name__ = l_("Stickers")
__module_emoji__ = "🧩"
__module_description__ = l_("Steal and manage personal sticker packs")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_("Clone stickers and media into your own sticker packs."),
        l_("Includes pack listing, default pack switching, and sticker management commands."),
    )
)

__export_private_only__ = True
__export__ = export_stickers

__handlers__ = (
    StickerStealHandler,
    StickerStealPackHandler,
    StickerGetStickerHandler,
    StickerDeleteStickerHandler,
    StickerDeletePackHandler,
    StickerSwitchDefaultPackHandler,
    StickerMyPacksHandler,
)

__stats__ = stickers_stats
