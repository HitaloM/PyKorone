from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.args import ArgumentSchema
from korone.db.repositories.sticker_pack import StickerPackRepository
from korone.modules.stickers.args import StickerPackTarget, StickerPackTargetArg
from korone.modules.stickers.utils import get_valid_user_packs
from korone.ui import Code, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.db.models.sticker_pack import StickerPackModel


@dataclass(frozen=True, slots=True)
class StickerSwitchArguments:
    target: StickerPackTarget


@flags.help(description=l_("Set your default sticker pack by index or name."))
@flags.disableable(name="switch")
class StickerSwitchDefaultPackHandler(KoroneMessageHandler[StickerSwitchArguments]):
    arguments = ArgumentSchema(StickerSwitchArguments, target=StickerPackTargetArg(l_("Pack index or name")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("switch"),)

    async def handle(self) -> None:
        if not self.event.from_user:
            await self.answer(template(_("Could not identify your user.")))
            return

        target = self.args.target

        owner_id = self.event.from_user.id
        packs = await get_valid_user_packs(self.bot, owner_id)
        if not packs:
            await self.answer(_("You don't have any tracked sticker packs yet."))
            return

        selected_pack = self.resolve_target_pack(packs, target)
        if not selected_pack:
            await self.answer(template(_("Could not find a pack with index or name: {value}"), value=Code(target.raw)))
            return

        if selected_pack.is_default:
            await self.answer(template(_("{pack} is already your default pack."), pack=selected_pack.title))
            return

        await StickerPackRepository.set_default_by_pack_id(owner_id, selected_pack.pack_id)
        await self.answer(template(_("Default sticker pack changed to {pack}."), pack=selected_pack.title))

    @staticmethod
    def resolve_target_pack(packs: list[StickerPackModel], target: StickerPackTarget) -> StickerPackModel | None:
        if target.index is not None:
            if target.index < len(packs):
                return packs[target.index]
            return None

        for pack in packs:
            if pack.title.casefold() == target.normalized_name:
                return pack

        return None
