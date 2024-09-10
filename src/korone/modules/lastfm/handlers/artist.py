# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.lastfm.utils.commons import (
    build_response_text,
    get_lastfm_user_or_reply,
    handle_lastfm_error,
)
from korone.modules.lastfm.utils.deezer_api import DeezerClient, DeezerError
from korone.modules.lastfm.utils.errors import LastFMError
from korone.modules.lastfm.utils.formatters import format_tags, name_with_link
from korone.modules.lastfm.utils.lastfm_api import LastFMClient
from korone.utils.i18n import gettext as _


@router.message(Command(commands=["lfmartist", "lart"]))
async def lfmartist_command(client: Client, message: Message) -> None:
    last_fm_user = await get_lastfm_user_or_reply(message)
    if not last_fm_user:
        return

    last_fm = LastFMClient()
    try:
        last_played = (await last_fm.get_recent_tracks(last_fm_user, limit=1))[0]
    except LastFMError as e:
        await handle_lastfm_error(message, e)
        return
    except IndexError:
        await message.reply(_("No recent tracks found for your LastFM account."))
        return

    artist_info = None
    with suppress(LastFMError):
        artist_info = await last_fm.get_artist_info(last_played.artist.name, last_fm_user)

    user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)
    text = build_response_text(
        user_link=user_link,
        now_playing=last_played.now_playing,
        entity_name=last_played.artist.name,
        entity_type="👨‍🎤",
        playcount=artist_info.playcount if artist_info else 0,
        tags=format_tags(artist_info) if artist_info and artist_info.tags else "",
    )

    with suppress(DeezerError):
        deezer = DeezerClient()
        artist = await deezer.get_artist(last_played.artist.name)
        if artist and (picture := artist.picture_xl or artist.picture_big):
            await message.reply_photo(photo=picture, caption=text)
            return

    await message.reply(text, disable_web_page_preview=True)
