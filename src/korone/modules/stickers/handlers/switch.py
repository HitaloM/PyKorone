from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import flags
from ass_tg.types import OptionalArg, TextArg
from stfu_tg import Code, Template

from korone.db.repositories.sticker_pack import StickerPackRepository
from korone.filters.cmd import CMDFilter
from korone.modules.stickers.utils import get_valid_user_packs
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric

    from korone.db.models.sticker_pack import StickerPackModel


@flags.help(description=l_("Switch your default sticker pack by index or name."))
@flags.disableable(name="switch")
class StickerSwitchDefaultPackHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"target": OptionalArg(TextArg(l_("Pack index or name")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("switch"),)

    async def handle(self) -> None:
        if not self.event.from_user:
            await self.event.reply(str(Template(_("Could not identify your user."))))
            return

        target = (self.data.get("target") or "").strip()
        if not target:
            await self.event.reply(
                str(Template(_("Usage: {command} {target}"), command=Code("/switch"), target=Code("1 | pack_name")))
            )
            return

        owner_id = self.event.from_user.id
        packs = await get_valid_user_packs(self.bot, owner_id)
        if not packs:
            await self.event.reply(_("You don't have any tracked sticker packs yet."))
            return

        selected_pack = self.resolve_target_pack(packs, target)
        if not selected_pack:
            await self.event.reply(
                str(Template(_("Could not find a pack with index or name: {value}"), value=Code(target)))
            )
            return

        if selected_pack.is_default:
            await self.event.reply(str(Template(_("{pack} is already your default pack."), pack=selected_pack.title)))
            return

        await StickerPackRepository.set_default_by_pack_id(owner_id, selected_pack.pack_id)
        await self.event.reply(str(Template(_("Default sticker pack changed to {pack}."), pack=selected_pack.title)))

    @staticmethod
    def resolve_target_pack(packs: list[StickerPackModel], target: str) -> StickerPackModel | None:
        if target.isdigit():
            index = int(target) - 1
            if 0 <= index < len(packs):
                return packs[index]
            return None

        normalized = target.casefold()
        for pack in packs:
            if pack.title.casefold() == normalized:
                return pack

        return None
