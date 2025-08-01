# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import re
from collections.abc import Sequence

from hydrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMedia,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from korone.modules.medias.utils.cache import MediaCache
from korone.utils.i18n import gettext as _


class BaseMediaHandler:
    @staticmethod
    def extract_url(text: str, pattern: re.Pattern) -> str | None:
        m = pattern.search(text)
        return m.group() if m else None

    @staticmethod
    def format_caption(media_list: Sequence[InputMedia], url: str, service_label: str) -> str:
        caption = media_list[-1].caption or ""
        if len(media_list) > 1:
            caption += f"\n<a href='{url}'>{_('Open in')} {service_label}</a>"

        return BaseMediaHandler.truncate_caption(caption)

    @staticmethod
    def truncate_caption(caption: str, max_length: int = 1024) -> str:
        if not caption:
            return ""

        if not isinstance(caption, str):
            caption = str(caption)

        if len(caption) <= max_length:
            return caption

        return caption[: max_length - 3] + "[...]"

    @staticmethod
    async def send_media(
        message: Message,
        media_list: Sequence[InputMedia],
        caption: str,
        url: str,
        service_label: str,
    ) -> Message | None:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{_('Open in')} {service_label}", url=url)]
        ])

        caption = BaseMediaHandler.truncate_caption(caption)

        if len(media_list) == 1:
            media = media_list[0]
            if isinstance(media, InputMediaPhoto):
                return await message.reply_photo(
                    media.media, caption=caption, reply_markup=keyboard
                )
            if isinstance(media, InputMediaVideo):
                thumb = media.thumb if getattr(media, "thumb", None) else None
                return await message.reply_video(
                    media.media, caption=caption, reply_markup=keyboard, thumb=thumb
                )
            return None

        media_list[-1].caption = caption
        return await message.reply_media_group(media_list)  # type: ignore

    @staticmethod
    async def cache_media(identifier: str, sent_message: Message, expire: int) -> None:
        await MediaCache(identifier).set(sent_message, expire=expire)
