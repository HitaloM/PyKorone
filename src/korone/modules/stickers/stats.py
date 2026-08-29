from korone.db.repositories.sticker_pack import StickerPackRepository
from korone.ui import Code, UIExpression, field, section


async def stickers_stats() -> UIExpression:
    owners = await StickerPackRepository.unique_owner_count()
    packs = await StickerPackRepository.total_count()
    return section("Stickers", field("Users with packs", Code(owners)), field("Tracked packs", Code(packs)))
