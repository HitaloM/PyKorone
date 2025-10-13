# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

from hydrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from korone.modules.medias.utils.cache import MediaCache
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    import re
    from collections.abc import Sequence

type MediaGroupItem = InputMediaPhoto | InputMediaVideo

MAX_MEDIA_GROUP_SIZE = 10


def ensure_url_scheme(url: str, default_scheme: str = "https") -> str:
    trimmed = url.strip()
    if not trimmed:
        return trimmed

    parsed = urlparse(trimmed)
    if parsed.scheme:
        return trimmed

    if trimmed.startswith("//"):
        return f"{default_scheme}:{trimmed}"

    return f"{default_scheme}://{trimmed}"


def extract_url(text: str, pattern: re.Pattern) -> str | None:
    match = pattern.search(text)
    return ensure_url_scheme(match.group()) if match else None


def format_caption(media_list: Sequence[MediaGroupItem], url: str, service_label: str) -> str:
    caption = media_list[-1].caption or ""
    if len(media_list) > 1:
        caption += f"\n<a href='{url}'>{_('Open in')} {service_label}</a>"

    return truncate_caption(caption)


def truncate_caption(caption: str, max_length: int = 1024) -> str:
    if not caption:
        return ""

    if not isinstance(caption, str):
        caption = str(caption)

    if len(caption) <= max_length:
        return caption

    return caption[: max_length - 3] + "[...]"


async def send_media(
    message: Message,
    media_list: Sequence[MediaGroupItem],
    caption: str,
    url: str,
    service_label: str,
) -> Message | list[Message] | None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{_('Open in')} {service_label}", url=url)]
    ])

    caption = truncate_caption(caption)

    if len(media_list) == 1:
        media = media_list[0]
        if isinstance(media, InputMediaPhoto):
            return await message.reply_photo(media.media, caption=caption, reply_markup=keyboard)
        if isinstance(media, InputMediaVideo):
            thumb = media.thumb if getattr(media, "thumb", None) else None
            return await message.reply_video(
                media.media, caption=caption, reply_markup=keyboard, thumb=thumb
            )
        return None

    media_items = cast("list[MediaGroupItem]", [*media_list])
    if not media_items:
        return None

    media_items[-1].caption = caption

    if len(media_items) <= MAX_MEDIA_GROUP_SIZE:
        return await message.reply_media_group(media=media_items)

    sent_messages: list[Message] = []
    for index in range(0, len(media_items), MAX_MEDIA_GROUP_SIZE):
        chunk = media_items[index : index + MAX_MEDIA_GROUP_SIZE]
        sent = await message.reply_media_group(media=chunk)
        sent_messages.extend(sent)

    return sent_messages or None


async def cache_media(identifier: str, sent_message: Message | list[Message], expire: int) -> None:
    await MediaCache(identifier).set(sent_message, expire=expire)
