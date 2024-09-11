# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import html

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.lastfm.utils.commons import get_lastfm_user_or_reply, handle_lastfm_error
from korone.modules.lastfm.utils.errors import LastFMError
from korone.modules.lastfm.utils.formatters import get_time_elapsed_str, name_with_link
from korone.modules.lastfm.utils.lastfm_api import LastFMClient
from korone.utils.i18n import gettext as _


@router.message(Command("lfmrecent"))
async def lfmrecent_command(client: Client, message: Message) -> None:
    last_fm_user = await get_lastfm_user_or_reply(message)
    if not last_fm_user:
        return

    last_fm = LastFMClient()
    try:
        recent_tracks = await last_fm.get_recent_tracks(last_fm_user, limit=6)
    except LastFMError as e:
        await handle_lastfm_error(message, e)
        return

    if not recent_tracks:
        await message.reply(_("No recent tracks found."))
        return

    last_played = recent_tracks[0]
    played_tracks = recent_tracks[1:6] if last_played.now_playing else recent_tracks[:5]
    user_link = name_with_link(
        name=html.escape(str(message.from_user.first_name)), username=last_fm_user
    )

    formatted_tracks = []
    if last_played.now_playing:
        formatted_tracks.extend((
            _("{user} is listening to:\n").format(user=user_link)
            + f"🎧 <i>{html.escape(last_played.artist.name)}</i> — "
            f"<b>{html.escape(last_played.name)}</b>",
            _("\nLast 5 plays:"),
        ))
    else:
        formatted_tracks.append(_("{user} was listening to:\n").format(user=user_link))

    formatted_tracks.extend(
        f"🎧 <i>{html.escape(track.artist.name)}</i> — "
        f"<b>{html.escape(track.name)}</b>{get_time_elapsed_str(track)}"
        for track in played_tracks
    )
    await message.reply("\n".join(formatted_tracks), disable_web_page_preview=True)
