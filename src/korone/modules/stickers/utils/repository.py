from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramBadRequest

from korone.db.repositories.sticker_pack import StickerPackRepository

from .pack import default_pack_title
from .telegram import is_stickerset_invalid

if TYPE_CHECKING:
    from aiogram import Bot

    from korone.db.models.sticker_pack import StickerPackModel


async def get_valid_user_packs(bot: Bot, owner_id: int) -> list[StickerPackModel]:
    packs = await StickerPackRepository.list_user_packs(owner_id)
    invalid_pack_ids: list[str] = []

    for pack in packs:
        try:
            await bot.get_sticker_set(pack.pack_id)
        except TelegramBadRequest as exc:
            if is_stickerset_invalid(exc):
                invalid_pack_ids.append(pack.pack_id)
                continue
            raise

    if invalid_pack_ids:
        await StickerPackRepository.delete_packs(invalid_pack_ids)
        packs = await StickerPackRepository.list_user_packs(owner_id)

    if packs and not any(pack.is_default for pack in packs):
        await StickerPackRepository.set_default_by_pack_id(owner_id, packs[0].pack_id)
        packs = await StickerPackRepository.list_user_packs(owner_id)

    return packs


async def get_default_or_generated_pack_title(owner_id: int, first_name: str | None) -> str:
    if default_pack := await StickerPackRepository.get_default_pack(owner_id):
        return default_pack.title
    return default_pack_title(first_name)
