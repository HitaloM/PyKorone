from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from stfu_tg import Code, Doc, Template

from korone.db.repositories.sticker_pack import StickerPackRepository
from korone.modules.utils_.message import is_real_reply
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Remove a sticker from one of your tracked packs."))
@flags.disableable(name="delsticker")
class StickerDeleteStickerHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("delsticker"),)

    async def handle(self) -> None:
        if not self.event.from_user:
            await self.event.reply(_("Could not identify your user."))
            return

        if not self.event.reply_to_message or not is_real_reply(self.event):
            await self.event.reply(
                str(
                    Doc(
                        _("Reply to a sticker from your own pack first."),
                        Template(_("Then use {command}."), command=Code("/delsticker")),
                    )
                )
            )
            return

        reply_sticker = self.event.reply_to_message.sticker
        if not reply_sticker or not reply_sticker.set_name:
            await self.event.reply(_("That reply is not a sticker from a sticker set."))
            return

        tracked_pack = await StickerPackRepository.get_by_pack_id(reply_sticker.set_name)
        if not tracked_pack or tracked_pack.owner_id != self.event.from_user.id:
            await self.event.reply(_("This sticker is not from one of your tracked packs."))
            return

        try:
            await self.bot.delete_sticker_from_set(sticker=reply_sticker.file_id)
        except TelegramBadRequest:
            await self.event.reply(_("Could not delete this sticker from the pack."))
            return

        await self.event.reply(
            str(Template(_("Sticker deleted successfully from {pack}."), pack=Code(tracked_pack.title)))
        )
