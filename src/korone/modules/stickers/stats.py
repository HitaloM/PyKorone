from stfu_tg import Code, KeyValue, Section

from korone.db.repositories.sticker_pack import StickerPackRepository
from korone.utils.i18n import gettext as _


async def stickers_stats() -> Section:
    owners = await StickerPackRepository.unique_owner_count()
    packs = await StickerPackRepository.total_count()
    return Section(
        KeyValue(_("Users with packs"), Code(owners)), KeyValue(_("Tracked packs"), Code(packs)), title=_("Stickers")
    )
