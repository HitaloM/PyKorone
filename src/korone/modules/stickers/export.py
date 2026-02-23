from typing import TYPE_CHECKING

from korone.db.repositories.sticker_pack import StickerPackRepository

if TYPE_CHECKING:
    from datetime import datetime


async def export_stickers(chat_id: int) -> dict[str, dict[str, list[dict[str, str | bool | datetime]]]]:
    packs = await StickerPackRepository.list_user_packs(chat_id)
    return {
        "stickers": {
            "packs": [
                {
                    "pack_id": pack.pack_id,
                    "title": pack.title,
                    "is_default": pack.is_default,
                    "created_at": pack.created_at,
                }
                for pack in packs
            ]
        }
    }
