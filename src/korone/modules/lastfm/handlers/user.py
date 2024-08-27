# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import LastFMClient, LastFMError, get_biggest_lastfm_image
from korone.modules.lastfm.utils.types import LastFMUser
from korone.utils.i18n import gettext as _


@router.message(Command("lfmuser"))
async def lfmuser_command(client: Client, message: Message) -> None:
    last_fm_user = await get_lastfm_user(message.from_user.id)
    if not last_fm_user:
        await message.reply(
            _(
                "You need to set your LastFM username first! "
                "Example: <code>/setlfm username</code>."
            )
        )
        return

    last_fm = LastFMClient()

    user_info = await fetch_user_info(last_fm, last_fm_user, message)
    if not user_info:
        return

    registered = datetime.fromtimestamp(user_info.registered, tz=UTC).strftime("%d-%m-%Y")
    user_mention = message.from_user.mention()
    image = await get_biggest_lastfm_image(user_info)

    text = format_user_info_text(user_mention, user_info, registered)

    if image:
        await message.reply_photo(photo=image, caption=text)
        return

    await message.reply(text, disable_web_page_preview=True)


async def fetch_user_info(
    last_fm: LastFMClient, last_fm_user: str, message: Message
) -> LastFMUser | None:
    try:
        return await last_fm.get_user_info(last_fm_user)
    except LastFMError as e:
        await handle_lastfm_error(e, message)
        return None


async def handle_lastfm_error(e: LastFMError, message: Message) -> None:
    if "User not found" in e.message:
        await message.reply(_("Your LastFM username was not found! Try setting it again."))
        return

    await message.reply(
        _(
            "An error occurred while fetching your LastFM data!"
            "\n<blockquote>{error}</blockquote>"
        ).format(error=e.message)
    )


def format_user_info_text(user_mention: str, user_info: LastFMUser, registered: str) -> str:
    return _(
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
