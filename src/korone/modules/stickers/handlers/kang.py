# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import hashlib
from pathlib import Path
from typing import Any

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.errors import PeerIdInvalid, StickersetInvalid, UserIsBlocked
from hydrogram.raw.functions.messages import GetStickerSet, SendMedia
from hydrogram.raw.functions.stickers import AddStickerToSet, CreateStickerSet
from hydrogram.raw.types import (
    DocumentAttributeFilename,
    InputDocument,
    InputMediaUploadedDocument,
    InputStickerSetItem,
    InputStickerSetShortName,
)
from hydrogram.types import Message, User

from korone import app_dir
from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.stickers.database import get_or_create_pack, update_user_pack
from korone.modules.stickers.utils import generate_random_file_path, resize_image, resize_video
from korone.utils.i18n import gettext as _


class KangHandler(MessageHandler):
    @router.message(Command(commands=["kang", "steal", "kibe"]))
    async def handle(self, client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        user = message.from_user

        emoji = self.extract_emoji(command, message)
        if not emoji or not message.reply_to_message:
            await message.reply(_("You need to reply to an image, video, or sticker."))
            return

        sent_message = await message.reply(_("Processing..."))

        media_type, file_id, file_extension = self.determine_media_type(message)
        if not (media_type and file_id and file_extension):
            await sent_message.edit(
                _("Invalid media type. Please reply to an image, video, or sticker.")
            )
            return

        file_name = Path(
            app_dir / f"downloads/{generate_random_file_path("file", file_extension)}"
        ).as_posix()

        file_path = await client.download_media(file_id, file_name=file_name)
        if not file_path:
            await sent_message.edit(_("Error downloading media."))
            return

        pack_num = await get_or_create_pack(user.id, media_type)
        resized_file = await self.resize_media(media_type, file_path)  # type: ignore

        if not resized_file:
            await sent_message.edit(_("Error processing media."))
            return

        mime_type, pack_name_suffix = self.determine_mime_type_and_suffix(media_type)
        pack_title, pack_name = self.generate_pack_names(user, client, pack_num, pack_name_suffix)
        pack_exists = await self.check_if_pack_exists(client, pack_name)

        if pack_exists and pack_exists.set.count > 119:
            pack_num[0]["num"] += 1
            await update_user_pack(user.id, media_type, pack_num[0]["num"])

        uploaded_file = await client.save_file(resized_file)  # type: ignore
        media = await self.send_media(client, message, uploaded_file, mime_type, file_extension)

        pack_info = {
            "client": client,
            "user": user,
            "media": media,
            "pack_name": pack_name,
            "emoji": emoji,
            "pack_title": pack_title,
            "pack_exists": pack_exists,
            "sent_message": sent_message,
        }

        if not await self.add_or_create_sticker_pack(pack_info):
            return

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=_("View pack"), url=f"https://t.me/addstickers/{pack_name}")
        await sent_message.edit(
            _("Sticker <b>successfully</b> added to pack\nEmoji: {sticker_emoji}").format(
                sticker_emoji=emoji
            ),
            reply_markup=keyboard.as_markup(),
        )

        Path(file_path).unlink(missing_ok=True)  # type: ignore
        Path(resized_file).unlink(missing_ok=True)

    @staticmethod
    def determine_mime_type_and_suffix(media_type: str) -> tuple[str, str]:
        return {
            "video": ("video/webm", "video"),
            "animated": ("application/x-tgsticker", "animated"),
        }.get(media_type, ("image/png", ""))

    @staticmethod
    def generate_pack_names(
        user, client: Client, pack_num: list, pack_name_suffix: str
    ) -> tuple[str, str]:
        pack_title = f"@{user.username}'s kang pack v{pack_num[0]["num"]} {pack_name_suffix}"
        user_id_hash = hashlib.sha1(bytearray(user.id)).hexdigest()
        pack_name_hash = hashlib.sha1(bytearray(pack_title.lower().encode())).hexdigest()
        pack_name = f"x{pack_name_hash[:10]}{user_id_hash[:10]}_by_{client.me.username}"  # type: ignore
        return pack_title, pack_name

    @staticmethod
    async def check_if_pack_exists(client: Client, pack_name: str) -> Any:
        try:
            return await client.invoke(
                GetStickerSet(
                    stickerset=InputStickerSetShortName(short_name=pack_name),  # type: ignore
                    hash=0,
                )
            )
        except StickersetInvalid:
            return False

    @staticmethod
    async def send_media(
        client: Client, message: Message, uploaded_file: Any, mime_type: str, file_extension: str
    ) -> Any:
        return await client.invoke(
            SendMedia(
                peer=await client.resolve_peer("-1001332080671"),  # type: ignore
                media=InputMediaUploadedDocument(
                    file=uploaded_file,
                    mime_type=mime_type,
                    attributes=[DocumentAttributeFilename(file_name=f"sticker{file_extension}")],  # type: ignore
                ),
                message=f"New #kang from {message.from_user.id}",
                random_id=client.rnd_id(),
            )
        )

    @staticmethod
    async def add_or_create_sticker_pack(pack_info: dict[str, Any]) -> bool:
        client: Client = pack_info["client"]
        media = pack_info["media"]
        pack_name: str = pack_info["pack_name"]
        emoji: str = pack_info["emoji"]
        pack_exists = pack_info["pack_exists"]
        sent_message: Message = pack_info["sent_message"]

        sticker_file = media.updates[-1].message.media.document
        try:
            if pack_exists:
                await sent_message.edit(_("Adding the sticker to the pack..."))
                await client.invoke(
                    AddStickerToSet(
                        stickerset=InputStickerSetShortName(short_name=pack_name),  # type: ignore
                        sticker=InputStickerSetItem(
                            document=InputDocument(
                                id=sticker_file.id,
                                access_hash=sticker_file.access_hash,
                                file_reference=sticker_file.file_reference,
                            ),  # type: ignore
                            emoji=emoji,
                        ),
                    )
                )
            else:
                await sent_message.edit(_("Creating the sticker pack..."))
                user: User = pack_info["user"]
                pack_title: str = pack_info["pack_title"]
                await client.invoke(
                    CreateStickerSet(
                        user_id=await client.resolve_peer(user.id),  # type: ignore
                        title=pack_title,
                        short_name=pack_name,
                        stickers=[
                            InputStickerSetItem(
                                document=InputDocument(
                                    id=sticker_file.id,
                                    access_hash=sticker_file.access_hash,
                                    file_reference=sticker_file.file_reference,
                                ),  # type: ignore
                                emoji=emoji,
                            )
                        ],
                    )
                )
        except (PeerIdInvalid, KeyError, UserIsBlocked):
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text=_("Start"), url=f"https://t.me/{client.me.username}?start")  # type: ignore
            await sent_message.edit(
                _(
                    "Oops, looks like I do not have enough permissions to create a sticker "
                    "pack for you!\n<b>Please start the bot first.</b>"
                ),
                reply_markup=keyboard.as_markup(),
            )
            return False
        except Exception as e:
            await sent_message.edit(_("An error occurred: {}").format(str(e)))
            return False

        return True

    @staticmethod
    def extract_emoji(command: CommandObject, message: Message) -> str | None:
        if command.args:
            return command.args.split(" ")[0]
        if message.reply_to_message and message.reply_to_message.sticker:
            return message.reply_to_message.sticker.emoji
        return "🤔"

    @staticmethod
    def determine_media_type(message: Message) -> tuple[str | None, str | None, str | None]:
        media_type = None
        file_id = None
        extension = None

        if photo := message.reply_to_message.photo:
            media_type = "photo"
            file_id = photo.file_id
            extension = ".png"
        elif video := message.reply_to_message.video:
            media_type = "video"
            file_id = video.file_id
            extension = ".mp4"
        elif animation := message.reply_to_message.animation:
            media_type = "video"
            file_id = animation.file_id
            extension = ".mp4"
        elif document := message.reply_to_message.document:
            if document.mime_type and "image" in document.mime_type:
                media_type = "photo"
                file_id = document.file_id
                extension = ".png"
            elif document.mime_type and "video" in document.mime_type:
                media_type = "video"
                file_id = document.file_id
                extension = ".mp4"
        elif sticker := message.reply_to_message.sticker:
            if sticker.is_animated:
                media_type = "animated"
                extension = ".tgs"
            elif sticker.is_video:
                media_type = "video"
                extension = ".webm"
            else:
                media_type = "photo"
                extension = ".webp"

            file_id = sticker.file_id
        return media_type, file_id, extension

    @staticmethod
    async def resize_media(media_type: str, file_path: str) -> str | None:
        if media_type in {"photo", "animated"}:
            return await asyncio.to_thread(resize_image, file_path)
        return await resize_video(file_path) if media_type == "video" else None
