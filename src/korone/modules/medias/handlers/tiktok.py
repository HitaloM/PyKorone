# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html
from datetime import timedelta
from typing import cast

from hairydogm.chat_action import ChatActionSender
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.filters import Regex
from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.common import extract_url, send_media
from korone.modules.medias.utils.tiktok.scraper import URL_PATTERN, fetch_tiktok_media
from korone.modules.medias.utils.tiktok.types import TikTokSlideshow, TikTokVideo
from korone.utils.i18n import gettext as _


@router.message(Regex(URL_PATTERN))
async def handle_tiktok(client, message: Message) -> None:
    if not message.text:
        return

    tiktok_url = extract_url(message.text, URL_PATTERN)
    if not tiktok_url:
        return

    result = await fetch_tiktok_media(tiktok_url)
    if not result:
        return

    media, media_type, media_id, media_obj = result

    if media_type == "video":
        media_list = [cast("InputMediaVideo", media)]
    else:
        media_list = cast("list[InputMediaPhoto]", media)

    caption = format_media_text(media_obj)
    cache = MediaCache(media_id)

    async with ChatActionSender(
        client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
    ):
        sent_message = await send_media(message, media_list, caption, tiktok_url, _("TikTok"))

    if sent_message:
        await cache.set(sent_message, int(timedelta(weeks=1).total_seconds()))


def format_media_text(media: TikTokVideo | TikTokSlideshow) -> str:
    text = f"<b>{media.author}{':' if media.desc else ''}</b>"
    if media.desc:
        escaped_desc = html.escape(media.desc[:900])
        text += f"\n{escaped_desc}{'...' if len(media.desc) > 900 else ''}"
    return text
