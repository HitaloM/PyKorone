# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import (
    DeezerClient,
    DeezerError,
    LastFMClient,
    LastFMError,
    format_tags,
    get_time_elapsed_str,
    name_with_link,
)
from korone.modules.lastfm.utils.types import DeezerData
from korone.utils.i18n import gettext as _


@router.message(Command(commands=["lfmartist", "lart"]))
async def lfmartist_command(client: Client, message: Message) -> None:
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

    if not (lastfm_data := await fetch_lastfm_data(last_fm, last_fm_user, message)):
        return

    last_played, artist_info = lastfm_data

    user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)
    text = build_response_text(user_link, last_played, artist_info)

    deezer = DeezerClient()
    artist = await fetch_deezer_artist(deezer, last_played.artist.name)

    if artist and (picture := artist.picture_xl or artist.picture_big):
        await message.reply_photo(photo=picture, caption=text)
        return

    await message.reply(text, disable_web_page_preview=True)


async def fetch_lastfm_data(
    last_fm: LastFMClient, last_fm_user: str, message: Message
) -> tuple | None:
    try:
        last_played = (await last_fm.get_recent_tracks(last_fm_user, limit=1))[0]
        artist_info = await last_fm.get_artist_info(last_played.artist.name, last_fm_user)
        return last_played, artist_info
    except LastFMError as e:
        await handle_lastfm_error(e, message)
        return None
    except IndexError:
        await message.reply(_("No recent tracks found for your LastFM account."))
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


def build_response_text(user_link: str, last_played, artist_info) -> str:
    if last_played.now_playing:
        text = _("{user}'s is listening to:\n").format(user=user_link)
    else:
        text = _("{user}'s was listening to:\n").format(user=user_link)

    text += "👨‍🎤 <b>{artist_name}</b>{time}{plays}".format(
        artist_name=last_played.artist.name,
        time="" if last_played.now_playing else get_time_elapsed_str(last_played),
        plays=_(" ∙ <code>{artist_playcount} plays</code>").format(
            artist_playcount=artist_info.playcount
        )
        if artist_info.playcount > 0
        else "",
    )

    if artist_info.tags:
        text += f"\n\n{format_tags(artist_info)}"

    return text


async def fetch_deezer_artist(deezer: DeezerClient, artist_name: str) -> DeezerData | None:
    try:
        return await deezer.get_artist(artist_name)
    except DeezerError:
        return None
