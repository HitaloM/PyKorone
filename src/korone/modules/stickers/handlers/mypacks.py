from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command
from stfu_tg import Code, Section, Template, Url

from korone.modules.stickers.utils import get_valid_user_packs
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("List your tracked sticker packs."))
@flags.disableable(name="mypacks")
class StickerMyPacksHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("mypacks"),)

    async def handle(self) -> None:
        if not self.event.from_user:
            await self.event.reply(_("Could not identify your user."))
            return

        packs = await get_valid_user_packs(self.bot, self.event.from_user.id)
        if not packs:
            await self.event.reply(_("You don't have any tracked sticker packs yet."))
            return

        lines: list[Template] = []
        for index, pack in enumerate(packs, start=1):
            pack_url = f"https://t.me/addstickers/{pack.pack_id}"
            default_mark = " ✓" if pack.is_default else ""
            lines.append(
                Template(
                    _("{index}. {pack}{default_mark}"),
                    index=Code(index),
                    pack=Url(pack.title, pack_url),
                    default_mark=default_mark,
                )
            )

        text = str(Section(*lines, title=Template(_("{name}'s sticker packs"), name=self.event.from_user.first_name)))
        await self.event.reply(text, disable_web_page_preview=True)
