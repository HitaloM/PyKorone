# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.lastfm.utils import (
    LastFMClient,
    fetch_and_handle_recent_track,
    get_entity_info,
    get_lastfm_user_or_reply,
    send_entity_response,
)


@router.message(Command(commands=["lfmartist", "lart"]))
async def lfmartist_command(client: Client, message: Message) -> None:
    last_fm_user = await get_lastfm_user_or_reply(message)
    if not last_fm_user:
        return

    track_data = await fetch_and_handle_recent_track(message, last_fm_user)
    if not track_data:
        return

    last_played, user_link = track_data
    last_fm = LastFMClient()

    artist_info = await get_entity_info(last_fm, last_played, last_fm_user, "artist")

    await send_entity_response(
        message,
        last_played,
        user_link,
        artist_info,
        "👨‍🎤",
        last_played.artist.name,
    )
