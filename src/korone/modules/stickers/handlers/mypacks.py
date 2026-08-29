from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.modules.stickers.utils import get_valid_user_packs
from korone.ui import Code, UIExpression, link, section, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("List sticker packs currently tracked for your account."))
@flags.disableable(name="mypacks")
class StickerMyPacksHandler(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("mypacks"),)

    async def handle(self) -> None:
        if not self.event.from_user:
            await self.event.reply(_("Could not identify your user."))
            return

        packs = await get_valid_user_packs(self.bot, self.event.from_user.id)
        if not packs:
            await self.event.reply(_("You don't have any tracked sticker packs yet."))
            return

        lines: list[UIExpression] = []
        for index, pack in enumerate(packs, start=1):
            pack_url = f"https://t.me/addstickers/{pack.pack_id}"
            default_mark = " ✓" if pack.is_default else ""
            lines.append(
                template(
                    _("{index}. {pack}{default_mark}"),
                    index=Code(index),
                    pack=link(pack.title, pack_url),
                    default_mark=default_mark,
                )
            )

        text = section(template(_("{name}'s sticker packs"), name=self.event.from_user.first_name), *lines)
        await self.answer(text, disable_web_page_preview=True)
