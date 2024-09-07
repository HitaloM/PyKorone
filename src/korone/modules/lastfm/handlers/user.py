# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.lastfm.utils.commons import get_lastfm_user_or_reply, handle_lastfm_error
from korone.modules.lastfm.utils.errors import LastFMError
from korone.modules.lastfm.utils.image_filter import get_biggest_lastfm_image
from korone.modules.lastfm.utils.lastfm_api import LastFMClient
from korone.utils.i18n import gettext as _


@router.message(Command("lfmuser"))
async def lfmuser_command(client: Client, message: Message) -> None:
    last_fm_user = await get_lastfm_user_or_reply(message)
    if not last_fm_user:
        return

    last_fm = LastFMClient()
    try:
        user_info = await last_fm.get_user_info(last_fm_user)
    except LastFMError as e:
        await handle_lastfm_error(message, e)
        return

    registered = datetime.fromtimestamp(user_info.registered, tz=UTC).strftime("%d-%m-%Y")
    user_mention = message.from_user.mention()
    image = await get_biggest_lastfm_image(user_info)

    text = _(
        "User: <b>{user}</b>\n\n"
        "Total scrobbles: <code>{playcount}</code>\n"
        "Tracks scrobbled: <code>{track_count}</code>\n"
        "Artists scrobbled: <code>{artist_count}</code>\n"
        "Albums scrobbled: <code>{album_count}</code>\n"
        "\nRegistered: <i>{registered}</i>"
    ).format(
        user=user_mention,
        playcount=user_info.playcount,
        track_count=user_info.track_count,
        artist_count=user_info.artist_count,
        album_count=user_info.album_count,
        registered=registered,
    )

    if image:
        await message.reply_photo(photo=image, caption=text)
        return

    await message.reply(text, disable_web_page_preview=True)
