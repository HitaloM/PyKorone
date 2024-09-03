# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import Message

from korone import constants
from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.stickers.database import get_or_create_pack, update_user_pack
from korone.modules.stickers.utils import (
    add_or_create_sticker_pack,
    check_if_pack_exists,
    check_video,
    determine_media_type,
    determine_mime_type_and_suffix,
    extract_emoji,
    generate_pack_names,
    generate_random_file_path,
    resize_media,
    send_media,
)
from korone.utils.i18n import gettext as _


@router.message(Command(commands=["kang", "steal", "kibe"]))
async def kang_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()
    user = message.from_user

    emoji = extract_emoji(command, message)
    if not emoji or not message.reply_to_message:
        await message.reply(_("You need to reply to an image, video, or sticker."))
        return

    sent_message = await message.reply(_("Processing..."))

    media_type, file_id, file_extension = determine_media_type(message)
    if not (media_type and file_id and file_extension):
        await sent_message.edit(
            _("Invalid media type. Please reply to an image, video, or sticker.")
        )
        return

    file_name = Path(
        constants.BOT_ROOT_PATH / f"downloads/{generate_random_file_path("file", file_extension)}"
    ).as_posix()

    file_path = await client.download_media(file_id, file_name=file_name)
    if not file_path:
        await sent_message.edit(_("Error downloading media."))
        return

    if media_type == "video" and not await check_video(sent_message, file_path):  # type: ignore
        Path(file_path).unlink(missing_ok=True)  # type: ignore
        return

    pack_num = await get_or_create_pack(user.id, media_type)
    resized_file = await resize_media(media_type, file_path)  # type: ignore

    if not resized_file:
        await sent_message.edit(_("Error processing media."))
        return

    mime_type, pack_name_suffix = determine_mime_type_and_suffix(media_type)
    pack_title, pack_name = generate_pack_names(user, client, pack_num, pack_name_suffix)
    pack_exists = await check_if_pack_exists(client, pack_name)

    if pack_exists and pack_exists.set.count > 119:
        pack_num[0]["num"] += 1
        await update_user_pack(user.id, media_type, pack_num[0]["num"])

    uploaded_file = await client.save_file(resized_file)  # type: ignore
    media = await send_media(client, message, uploaded_file, mime_type, file_extension)

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

    if not await add_or_create_sticker_pack(pack_info):
        return

    keyboard = InlineKeyboardBuilder().button(
        text=_("View pack"), url=f"https://t.me/addstickers/{pack_name}"
    )
    await sent_message.edit(
        _("Sticker <b>successfully</b> added to pack\nEmoji: {sticker_emoji}").format(
            sticker_emoji=emoji
        ),
        reply_markup=keyboard.as_markup(),
    )

    Path(file_path).unlink(missing_ok=True)  # type: ignore
    Path(resized_file).unlink(missing_ok=True)
