# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

from hairydogm.chat_action import ChatActionSender
from hydrogram.client import Client
from hydrogram.enums import ChatAction
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Regex
from korone.modules.medias.utils.bluesky.api import fetch_bluesky, get_username_and_post_id
from korone.modules.medias.utils.common import cache_media, extract_url, format_caption, send_media
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(
    r"""
    (?:(?:https?://))?
    (?:www\.)?
    bsky\.app
    /
    .+?(?=\s|$)
    """,
    re.VERBOSE | re.IGNORECASE,
)


@router.message(Regex(URL_PATTERN))
async def handle_bluesky_message(client: Client, message: Message) -> None:
    if not message.text:
        return

    url = extract_url(message.text, URL_PATTERN)
    if not url:
        return

    media_list = await fetch_bluesky(url)
    if not media_list:
        return

    caption = format_caption(media_list, url, _("BlueSky"))

    async with ChatActionSender(
        client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
    ):
        sent_message = await send_media(message, media_list, caption, url, _("BlueSky"))

    post_id = get_username_and_post_id(url)[1]
    if post_id and sent_message:
        await cache_media(post_id, sent_message, int(timedelta(weeks=1).total_seconds()))
