from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command
from stfu_tg import Code, Doc, Template

from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Explain how to delete sticker packs."))
@flags.disableable(name="delpack")
class StickerDeletePackHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("delpack"),)

    async def handle(self) -> None:
        doc = Doc(
            _("Telegram bots cannot delete entire sticker packs directly."),
            Template(
                _("Delete packs manually via {bot}, then run {command} to refresh your list."),
                bot=Code("@stickers"),
                command=Code("/mypacks"),
            ),
            Template(_("Tip: use {command} to switch your default pack."), command=Code("/switch")),
        )
        await self.event.reply(str(doc))
