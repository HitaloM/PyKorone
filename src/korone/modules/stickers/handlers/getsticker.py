from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile
from stfu_tg import Code, Doc, KeyValue, Template, Url

from korone.filters.cmd import CMDFilter
from korone.modules.stickers.utils import download_file, suffix_from_sticker
from korone.modules.utils_.message import is_real_reply
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Sticker


@flags.help(description=l_("Send a replied sticker as a document with basic sticker information."))
@flags.disableable(name="getsticker")
class StickerGetStickerHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("getsticker"),)

    async def handle(self) -> None:
        if not self.event.reply_to_message or not is_real_reply(self.event):
            await self.event.reply(
                str(Template(_("Reply to a sticker first, then use {command}."), command=Code("/getsticker")))
            )
            return

        sticker = self.event.reply_to_message.sticker
        if not sticker:
            await self.event.reply(_("That reply is not a sticker."))
            return

        if sticker.is_animated:
            await self.event.reply(_("Animated stickers are not supported by this command."))
            return

        with TemporaryDirectory(prefix="korone-getsticker-") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            suffix = suffix_from_sticker(sticker)
            filename = f"sticker-{sticker.file_unique_id}{suffix}"
            file_path = temp_dir / filename

            try:
                await download_file(self.bot, sticker.file_id, file_path)

                caption = str(self.build_sticker_info_doc(sticker))
                await self.event.reply_document(
                    document=FSInputFile(file_path, filename=filename),
                    caption=caption,
                    disable_content_type_detection=True,
                )
            except OSError, RuntimeError, TelegramBadRequest:
                await self.event.reply(_("Could not fetch this sticker file."))

    @staticmethod
    def build_sticker_info_doc(sticker: Sticker) -> Doc:
        _("video") if sticker.is_video else _("animated") if sticker.is_animated else _("static")
        info = Doc(KeyValue(_("Emoji"), sticker.emoji or _("none")), KeyValue(_("ID"), Code(sticker.file_id)))

        if sticker.set_name:
            pack_url = f"https://t.me/addstickers/{sticker.set_name}"
            info += KeyValue(_("Pack"), Url(sticker.set_name, pack_url))

        return info
