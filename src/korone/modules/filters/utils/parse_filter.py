# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from cashews import suppress
from hydrogram.enums import MessageMediaType
from hydrogram.types import Message

from korone.utils.i18n import gettext as _

from .types import Button, FilterFile, Saveable

MESSAGE_LENGTH_LIMIT = 4096

SUPPORTED_MEDIA_TYPES = {
    MessageMediaType.PHOTO: "photo",
    MessageMediaType.VIDEO: "video",
    MessageMediaType.AUDIO: "audio",
    MessageMediaType.VOICE: "voice",
    MessageMediaType.DOCUMENT: "document",
    MessageMediaType.STICKER: "sticker",
    MessageMediaType.ANIMATION: "animation",
}


async def get_file_info(message: Message) -> FilterFile | None:
    for media_type, media_name in SUPPORTED_MEDIA_TYPES.items():
        media_attr = getattr(message, str(media_type.value), None)
        if media_attr:
            file_id = getattr(media_attr, "file_id", None)
            if file_id:
                return FilterFile(id=file_id, type=media_name)

    with suppress(ValueError):
        if media_group := await message.get_media_group():
            last_message = media_group[-1]
            for media_type, media_name in SUPPORTED_MEDIA_TYPES.items():
                media_attr = getattr(last_message, str(media_type.value), None)
                if media_attr:
                    file_id = getattr(media_attr, "file_id", None)
                    if file_id:
                        return FilterFile(id=file_id, type=media_name)

    return None


async def parse_replied_message(
    message: Message,
    replied_message: Message,
) -> tuple[str | None, FilterFile | None, list[list[Button]] | None]:
    if replied_message.media and replied_message.media not in SUPPORTED_MEDIA_TYPES:
        await message.reply(
            _("Please check the Filters documentation for the list of the allowed content types.")
        )
        return None, None, None

    if replied_message.text:
        message_text = replied_message.text.html
    elif replied_message.caption:
        message_text = replied_message.caption.html
    else:
        message_text = ""

    if not message_text and not replied_message.media:
        await message.reply(_("The text of the replied message is empty."))
        return None, None, None

    file_info = await get_file_info(replied_message)
    buttons: list[list[Button]] = []

    return message_text, file_info, buttons


async def parse_saveable(
    message: Message, text: str | None, allow_reply_message: bool = True
) -> Saveable | None:
    combined_text = text or ""
    buttons: list[list[Button]] = []
    file_info: FilterFile | None = None

    if message.reply_to_message and allow_reply_message:
        reply_text, file_info, reply_buttons = await parse_replied_message(
            message, message.reply_to_message
        )
        if reply_buttons:
            buttons.extend(reply_buttons)

        combined_text = f"{reply_text}\n{combined_text}" if reply_text else combined_text
    else:
        file_info = await get_file_info(message)

    if len(combined_text) > MESSAGE_LENGTH_LIMIT:
        await message.reply(
            _("The maximum length of the filter is {length} characters.").format(
                length=MESSAGE_LENGTH_LIMIT
            )
        )
        return None

    return Saveable(text=combined_text, file=file_info, buttons=buttons)
