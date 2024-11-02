# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import hashlib
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

from korone.config import ConfigManager
from korone.utils.i18n import gettext as _

LOGS_CHAT = ConfigManager.get("korone", "LOGS_CHAT")


def generate_pack_names(
    user: User, client: Client, pack_num: list, pack_name_suffix: str
) -> tuple[str, str]:
    pack_title = f"@{user.username}'s kang pack v{pack_num[0]['num']} {pack_name_suffix}"
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
            peer=await client.resolve_peer(str(LOGS_CHAT)),  # type: ignore
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
