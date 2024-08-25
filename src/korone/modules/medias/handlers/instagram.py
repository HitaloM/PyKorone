# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram.client import Client
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.filters import Regex
from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.instagram import POST_PATTERN, instagram
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/.*?(?=\s|$)")


@router.message(Regex(URL_PATTERN))
async def handle_instagram(client: Client, message: Message) -> None:
    if not message.text:
        return

    match = URL_PATTERN.search(message.text)
    url = match.group() if match else None
    if not url:
        return

    media_list = await instagram(url)
    if not media_list:
        return

    if len(media_list) > 10:
        media_list = media_list[:10]

    caption = media_list[-1].caption
    if len(media_list) > 1:
        caption += f"\n<a href='{url}'>📷 {_("Open in Instagram")}</a>"

    async with ChatActionSender(
        client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
    ):
        if len(media_list) == 1:
            media = media_list[0]
            keyboard = (
                InlineKeyboardBuilder()
                .button(text=f"📷 {_("Open in Instagram")}", url=url)
                .as_markup()
            )
            if isinstance(media, InputMediaPhoto):
                sent_message = await message.reply_photo(
                    media.media, caption=caption, reply_markup=keyboard
                )
            elif isinstance(media, InputMediaVideo):
                sent_message = await message.reply_video(
                    media.media, caption=caption, reply_markup=keyboard
                )
            else:
                sent_message = None
        else:
            media_list[-1].caption = caption
            sent_message = await message.reply_media_group(media_list)  # type: ignore

    post_id_match = POST_PATTERN.search(url)
    post_id = post_id_match.group(1) if post_id_match else None
    if post_id and sent_message:
        cache = MediaCache(post_id)
        await cache.set(sent_message, expire=int(timedelta(weeks=1).total_seconds()))
