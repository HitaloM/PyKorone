from korone.db.repositories.sticker_pack import StickerPackRepository
from korone.utils.formatting import Code, KeyValue, Section


async def stickers_stats() -> Section:
    owners = await StickerPackRepository.unique_owner_count()
    packs = await StickerPackRepository.total_count()
    return Section(KeyValue("Users with packs", Code(owners)), KeyValue("Tracked packs", Code(packs)), title="Stickers")
