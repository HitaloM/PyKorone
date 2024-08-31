# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import hashlib
from pathlib import Path
from typing import Any

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
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, User

from korone.filters import CommandObject
from korone.utils.i18n import gettext as _

from .ffmpeg import ffprobe, resize_image, resize_video


def determine_mime_type_and_suffix(media_type: str) -> tuple[str, str]:
    return {
        "video": ("video/webm", "video"),
        "animated": ("application/x-tgsticker", "animated"),
    }.get(media_type, ("image/png", ""))


def generate_pack_names(
    user: User, client: Client, pack_num: list, pack_name_suffix: str
) -> tuple[str, str]:
    pack_title = f"@{user.username}'s kang pack v{pack_num[0]["num"]} {pack_name_suffix}"
    user_id_hash = hashlib.sha1(
        user.id.to_bytes((user.id.bit_length() + 7) // 8, "big")
    ).hexdigest()
    pack_name_hash = hashlib.sha1(pack_title.lower().encode()).hexdigest()
    pack_name = f"x{pack_name_hash[:10]}{user_id_hash[:10]}_by_{client.me.username}"  # type: ignore
    return pack_title, pack_name


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
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=_("Start"), url=f"https://t.me/{client.me.username}?start")]  # type: ignore
        ])
        await sent_message.edit(
            _(
                "Oops, looks like I do not have enough permissions to create a sticker "
                "pack for you!\n<b>Please start the bot first.</b>"
            ),
            reply_markup=keyboard,
        )
        return False
    except Exception as e:
        await sent_message.edit(_("An error occurred: {}").format(str(e)))
        return False

    return True


def extract_emoji(command: CommandObject, message: Message) -> str | None:
    if command.args:
        return command.args.split(" ")[0]
    if message.reply_to_message and message.reply_to_message.sticker:
        return message.reply_to_message.sticker.emoji
    return "🤔"


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


async def check_video(message: Message, file_path: str) -> bool:
    duration_str = await ffprobe(file_path)

    if not duration_str:
        await message.edit(_("Failed to get video information."))
        return False

    try:
        duration = float(duration_str)
    except (ValueError, IndexError) as e:
        await message.reply(_("Error parsing video information: {error}").format(error=str(e)))
        return False

    size = Path(file_path).stat().st_size

    if duration > 3:
        await message.edit(
            _("The video is too long ({duration}s)!\nMax duration is 3 seconds.").format(
                duration=duration
            )
        )
        return False

    if size > 256000:
        await message.edit(
            _("The video is too big ({size}KB)!\nMax size is 256KB").format(size=size / 1000)
        )
        return False

    return True


async def resize_media(media_type: str, file_path: str) -> str | None:
    if media_type in {"photo", "animated"}:
        return await asyncio.to_thread(resize_image, file_path)

    return await resize_video(file_path)
