# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from cashews import suppress
from hydrogram.enums import MessageMediaType
from hydrogram.types import Message

from korone.utils.i18n import gettext as _

from .types import Button, FilterFile, Saveable

MESSAGE_LENGTH_LIMIT = 4096

SUPPORTED_CONTENTS = {
    MessageMediaType.PHOTO: "photo",
    MessageMediaType.VIDEO: "video",
    MessageMediaType.AUDIO: "audio",
    MessageMediaType.VOICE: "voice",
    MessageMediaType.DOCUMENT: "document",
    MessageMediaType.STICKER: "sticker",
    MessageMediaType.ANIMATION: "animation",
}


async def extract_file_info(message: Message) -> FilterFile | None:
    if not message:
        return None

    content_type = next(
        (
            content_type
            for media_type, content_type in SUPPORTED_CONTENTS.items()
            if getattr(message, str(media_type.value), None)
        ),
        None,
    )

    if not content_type:
        return None

    with suppress(ValueError):
        if media_group := await message.get_media_group():
            message = media_group[-1]

    file_attr = getattr(message, str(content_type), None)
    file_id = file_attr.file_id if file_attr and hasattr(file_attr, "file_id") else None

    return FilterFile(id=file_id, type=content_type) if file_id else None


async def parse_reply_message(
    message: Message,
    replied_message: Message,
) -> tuple[str | None, FilterFile | None, list[list[Button]] | None]:
    if replied_message.media is not None:
        if replied_message.media not in SUPPORTED_CONTENTS:
            await message.reply(
                _(
                    "Please check the notes documentation for "
                    "the list of the allowed content types."
                )
            )
            return None, None, None
    elif replied_message.text is None and replied_message.caption is None:
        await message.reply(_("The text of the replied message is empty."))
        return None, None, None

    text = (
        replied_message.text.html
        if replied_message.text
        else replied_message.caption.html
        if replied_message.caption
        else ""
    )
    file_info = await extract_file_info(replied_message)
    buttons: list[list[Button]] = []

    return text, file_info, buttons


async def parse_saveable(
    message: Message, text: str | None, allow_reply_message: bool = True
) -> Saveable | None:
    note_text = text or ""
    buttons: list[list[Button]] = []
    file_data: FilterFile | None = None

    if message.reply_to_message and allow_reply_message:
        reply_text, file_data, reply_buttons = await parse_reply_message(
            message, message.reply_to_message
        )
        if reply_buttons:
            buttons.extend(reply_buttons)

        note_text = f"{reply_text}\n{note_text}" if reply_text else note_text
    else:
        file_data = await extract_file_info(message)

    if len(note_text) > MESSAGE_LENGTH_LIMIT:
        await message.reply(
            _("The maximum length of the note is {length} characters.").format(
                length=MESSAGE_LENGTH_LIMIT
            )
        )
        return None

    return Saveable(text=note_text, file=file_data, buttons=buttons)
