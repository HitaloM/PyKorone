import asyncio
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.filters import Command

from korone.args import ArgumentSchema
from korone.db.repositories.sticker_pack import StickerPackRepository
from korone.modules.stickers.args import StickerPackTitleArg
from korone.modules.stickers.utils import (
    DEFAULT_EMOJI,
    StickerPrepareError,
    build_pack_id,
    create_input_sticker,
    download_file,
    is_pack_full_error,
    is_stickerset_invalid,
    map_pack_write_error,
    prepare_sticker_file,
    suffix_from_sticker,
)
from korone.modules.utils_.message import is_real_reply
from korone.modules.utils_.reply_or_edit import edit_message_text
from korone.ui import Code, column, link, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_
from korone.utils.i18n import ngettext as pl_

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Sticker


@dataclass(frozen=True, slots=True)
class StickerStealPackArguments:
    pack_name: str


@flags.help(description=l_("Copy an entire sticker set into one of your packs."))
@flags.disableable(name="stealpack")
@flags.defer_sticker_pack_processing
class StickerStealPackHandler(KoroneMessageHandler[StickerStealPackArguments]):
    arguments = ArgumentSchema(StickerStealPackArguments, pack_name=StickerPackTitleArg(l_("Target pack name")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("kangpack", "stealpack"),)

    @staticmethod
    async def _retry_after_flood_control[R](operation: Callable[[], Awaitable[R]]) -> R:
        while True:
            try:
                return await operation()
            except TelegramRetryAfter as error:
                await asyncio.sleep(error.retry_after)

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
                await self._retry_after_flood_control(
                    lambda: self.bot.add_sticker_to_set(user_id=user_id, name=pack_id, sticker=input_sticker)
                )
                return pack_ready

            try:
                await self._retry_after_flood_control(
                    lambda: self.bot.add_sticker_to_set(user_id=user_id, name=pack_id, sticker=input_sticker)
                )
            except TelegramBadRequest as exc:
                if not is_stickerset_invalid(exc):
                    raise
                await self._retry_after_flood_control(
                    lambda: self.bot.create_new_sticker_set(
                        user_id=user_id,
                        name=pack_id,
                        title=pack_title,
                        stickers=[input_sticker],
                        sticker_type="regular",
                        sticker_format=sticker_format,
                    )
                )

        return True

    async def handle(self) -> None:
        if not self.event.from_user:
            await self.event.reply(_("Could not identify your user."))
            return

        if not self.event.reply_to_message or not is_real_reply(self.event):
            await self.answer(
                column(
                    _("Reply to a sticker from the source pack first."),
                    template(_("Then use {command}."), command=Code("/stealpack")),
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

        pack_title = self.args.pack_name
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
                await edit_message_text(
                    status_message,
                    template(_("Stealing sticker pack... {current}/{total}"), current=Code(index), total=Code(total)),
                )

        if not pack_ready:
            await status_message.edit_text(_("Could not add any sticker from that pack."))
            return

        await StickerPackRepository.upsert_pack(pack_id, user.id, pack_title, set_default=None)
        pack_url = f"https://t.me/addstickers/{pack_id}"

        if stopped_because_full:
            await edit_message_text(
                status_message,
                column(
                    template(
                        pl_(
                            "Target pack got full after {added} sticker.",
                            "Target pack got full after {added} stickers.",
                            added,
                        ),
                        added=Code(added),
                    ),
                    template(_("Pack: {pack}"), pack=link(pack_title, pack_url)),
                ),
                disable_web_page_preview=True,
            )
            return

        if skipped:
            await edit_message_text(
                status_message,
                column(
                    template(
                        pl_("Added {added}/{total} sticker.", "Added {added}/{total} stickers.", total),
                        added=Code(added),
                        total=Code(total),
                    ),
                    template(_("Skipped: {skipped}"), skipped=Code(skipped)),
                    template(_("Pack: {pack}"), pack=link(pack_title, pack_url)),
                ),
                disable_web_page_preview=True,
            )
            return

        await edit_message_text(
            status_message,
            column(
                _("Sticker pack copied successfully."), template(_("Pack: {pack}"), pack=link(pack_title, pack_url))
            ),
            disable_web_page_preview=True,
        )
