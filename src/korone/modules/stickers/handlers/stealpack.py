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
    is_pack_full_error,
    is_stickerset_invalid,
    map_pack_write_error,
    normalize_pack_title,
    prepare_sticker_file,
    suffix_from_sticker,
)
from korone.modules.utils_.message import is_real_reply
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message, Sticker
    from ass_tg.types.base_abc import ArgFabric


@flags.help(description=l_("Steal an entire sticker set into your own pack."))
@flags.disableable(name="stealpack")
class StickerStealPackHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"pack_name": OptionalArg(TextArg(l_("Target pack name")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("kangpack", "stealpack"),)

    async def _copy_single_sticker(
        self, *, source_sticker: Sticker, user_id: int, pack_id: str, pack_title: str, pack_ready: bool
    ) -> bool:
        with TemporaryDirectory(prefix="korone-pack-") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source_path = temp_dir / f"source{suffix_from_sticker(source_sticker)}"
            await download_file(self.bot, source_sticker.file_id, source_path)

            prepared_path, sticker_format = await prepare_sticker_file(source_path)
            input_sticker = create_input_sticker(
                prepared_path, sticker_format=sticker_format, emoji=source_sticker.emoji or DEFAULT_EMOJI
            )

            if pack_ready:
                await self.bot.add_sticker_to_set(user_id=user_id, name=pack_id, sticker=input_sticker)
                return pack_ready

            try:
                await self.bot.add_sticker_to_set(user_id=user_id, name=pack_id, sticker=input_sticker)
            except TelegramBadRequest as exc:
                if not is_stickerset_invalid(exc):
                    raise
                await self.bot.create_new_sticker_set(
                    user_id=user_id,
                    name=pack_id,
                    title=pack_title,
                    stickers=[input_sticker],
                    sticker_type="regular",
                    sticker_format=sticker_format,
                )

        return True

    async def handle(self) -> None:
        if not self.event.from_user:
            await self.event.reply(_("Could not identify your user."))
            return

        pack_title_arg = (self.data.get("pack_name") or "").strip()
        if not pack_title_arg:
            await self.event.reply(
                str(
                    Template(
                        _("Usage: {command} {pack_name}"), command=Code("/stealpack"), pack_name=Code("new_pack_name")
                    )
                )
            )
            return

        if not self.event.reply_to_message or not is_real_reply(self.event):
            await self.event.reply(
                str(
                    Doc(
                        _("Reply to a sticker from the source pack first."),
                        Template(_("Then use {command}."), command=Code("/stealpack")),
                    )
                )
            )
            return

        reply_sticker = self.event.reply_to_message.sticker
        if not reply_sticker or not reply_sticker.set_name:
            await self.event.reply(_("Reply to a sticker that belongs to a sticker set."))
            return

        status_message = await self.event.reply(_("Stealing sticker pack..."))
        user = self.event.from_user

        try:
            source_pack = await self.bot.get_sticker_set(reply_sticker.set_name)
        except TelegramBadRequest as exc:
            if is_stickerset_invalid(exc):
                await status_message.edit_text(_("The source sticker pack does not exist anymore."))
                return
            await status_message.edit_text(map_pack_write_error(exc))
            return

        pack_title = normalize_pack_title(pack_title_arg)
        bot_user = await self.bot.me()
        pack_id = build_pack_id(user.id, pack_title, bot_user.username)

        pack_ready = False
        added = 0
        skipped = 0
        stopped_because_full = False
        total = len(source_pack.stickers)

        for index, source_sticker in enumerate(source_pack.stickers, start=1):
            try:
                pack_ready = await self._copy_single_sticker(
                    source_sticker=source_sticker,
                    user_id=user.id,
                    pack_id=pack_id,
                    pack_title=pack_title,
                    pack_ready=pack_ready,
                )
                added += 1
            except StickerPrepareError:
                skipped += 1
            except TelegramBadRequest as exc:
                if is_pack_full_error(exc):
                    stopped_because_full = True
                    break
                if not pack_ready:
                    await status_message.edit_text(map_pack_write_error(exc))
                    return
                skipped += 1

            if index % 10 == 0 or index == total:
                await status_message.edit_text(
                    str(
                        Template(
                            _("Stealing sticker pack... {current}/{total}"), current=Code(index), total=Code(total)
                        )
                    )
                )

        if not pack_ready:
            await status_message.edit_text(_("Could not add any sticker from that pack."))
            return

        await StickerPackRepository.upsert_pack(pack_id, user.id, pack_title, set_default=None)
        pack_url = f"https://t.me/addstickers/{pack_id}"

        if stopped_because_full:
            await status_message.edit_text(
                str(
                    Doc(
                        Template(_("Target pack got full after {added} stickers."), added=Code(added)),
                        Template(_("Pack: {pack}"), pack=Url(pack_title, pack_url)),
                    )
                ),
                disable_web_page_preview=True,
            )
            return

        if skipped:
            await status_message.edit_text(
                str(
                    Doc(
                        Template(_("Added {added}/{total} stickers."), added=Code(added), total=Code(total)),
                        Template(_("Skipped: {skipped}"), skipped=Code(skipped)),
                        Template(_("Pack: {pack}"), pack=Url(pack_title, pack_url)),
                    )
                ),
                disable_web_page_preview=True,
            )
            return

        await status_message.edit_text(
            str(
                Doc(_("Sticker pack copied successfully."), Template(_("Pack: {pack}"), pack=Url(pack_title, pack_url)))
            ),
            disable_web_page_preview=True,
        )
