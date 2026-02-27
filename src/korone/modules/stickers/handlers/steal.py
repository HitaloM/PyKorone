from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from ass_tg.types import OptionalArg, TextArg
from stfu_tg import Code, Doc, Template, Url

from korone.db.repositories.sticker_pack import StickerPackRepository
from korone.modules.stickers.utils import (
    DEFAULT_EMOJI,
    StickerPrepareError,
    build_pack_id,
    create_input_sticker,
    download_file,
    extract_reply_media,
    get_default_or_generated_pack_title,
    is_stickerset_invalid,
    map_pack_write_error,
    parse_pack_and_emoji,
    prepare_sticker_file,
)
from korone.modules.utils_.message import is_real_reply
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


@flags.help(description=l_("Copy a replied sticker or media item into one of your packs."))
@flags.disableable(name="steal")
class StickerStealHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"args": OptionalArg(TextArg(l_("Pack name and optional emoji")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("kang", "steal"),)

    async def handle(self) -> None:
        if not self.event.from_user:
            await self.event.reply(_("Could not identify your user."))
            return

        if not self.event.reply_to_message or not is_real_reply(self.event):
            await self.event.reply(
                str(
                    Doc(
                        _("Reply to a sticker, photo, animation, video, or document first."),
                        Template(_("Then use {command}."), command=Code("/steal")),
                    )
                )
            )
            return

        status_message = await self.event.reply(_("Stealing sticker..."))
        user = self.event.from_user
        args_text = (self.data.get("args") or "").strip()

        try:
            file_id, suffix, reply_emoji = extract_reply_media(self.event)
        except ValueError:
            await status_message.edit_text(_("That reply does not contain supported media."))
            return

        default_title = await get_default_or_generated_pack_title(user.id, user.first_name)
        default_emoji = reply_emoji or DEFAULT_EMOJI
        pack_title, emoji = parse_pack_and_emoji(args_text, default_title=default_title, default_emoji=default_emoji)

        bot_user = await self.bot.me()
        pack_id = build_pack_id(user.id, pack_title, bot_user.username)
        created_new_pack = False

        try:
            with TemporaryDirectory(prefix="korone-sticker-") as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                source_path = temp_dir / f"source{suffix}"
                await download_file(self.bot, file_id, source_path)

                prepared_path, sticker_format = await prepare_sticker_file(source_path)
                input_sticker = create_input_sticker(prepared_path, sticker_format=sticker_format, emoji=emoji)

                try:
                    await self.bot.add_sticker_to_set(user_id=user.id, name=pack_id, sticker=input_sticker)
                except TelegramBadRequest as exc:
                    if not is_stickerset_invalid(exc):
                        await status_message.edit_text(map_pack_write_error(exc))
                        return

                    await self.bot.create_new_sticker_set(
                        user_id=user.id,
                        name=pack_id,
                        title=pack_title,
                        stickers=[input_sticker],
                        sticker_type="regular",
                        sticker_format=sticker_format,
                    )
                    created_new_pack = True
        except StickerPrepareError as exc:
            await status_message.edit_text(str(exc))
            return
        except TelegramBadRequest as exc:
            await status_message.edit_text(map_pack_write_error(exc))
            return

        await StickerPackRepository.upsert_pack(pack_id, user.id, pack_title, set_default=None)

        pack_url = f"https://t.me/addstickers/{pack_id}"
        if created_new_pack:
            response = Doc(_("Created new sticker pack."), Template(_("Pack: {pack}"), pack=Url(pack_title, pack_url)))
        else:
            response = Doc(
                _("Sticker saved successfully."), Template(_("Pack: {pack}"), pack=Url(pack_title, pack_url))
            )

        await status_message.edit_text(str(response), disable_web_page_preview=True)
