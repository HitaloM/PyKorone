# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import LastFMClient, LastFMError, get_time_elapsed_str
from korone.modules.lastfm.utils.formatters import name_with_link
from korone.utils.i18n import gettext as _


@router.message(Command("lfmrecent"))
async def lfmrecent_command(client: Client, message: Message) -> None:
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
    try:
        recent_tracks = await last_fm.get_recent_tracks(last_fm_user, limit=6)
    except LastFMError as e:
        error_message = (
            _("Your LastFM username was not found! Try setting it again.")
            if "User not found" in e.message
            else _(
                "An error occurred while fetching your LastFM data!"
                "\n<blockquote>{error}</blockquote>"
            ).format(error=e.message)
        )
        await message.reply(error_message)
        return

    if not recent_tracks:
        await message.reply(_("No recent tracks found."))
        return

    last_played = recent_tracks[0]
    played_tracks = recent_tracks[1:6] if last_played.now_playing else recent_tracks[:5]
    user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)

    formatted_tracks = []
    if last_played.now_playing:
        formatted_tracks.extend((
            _("{user} is listening to:\n").format(user=user_link)
            + f"🎧 <i>{last_played.artist.name}</i> — <b>{last_played.name}</b>",
            _("\nLast 5 plays:"),
        ))
    else:
        formatted_tracks.append(_("{user} was listening to:\n").format(user=user_link))

    formatted_tracks.extend(
        f"🎧 <i>{track.artist.name}</i> — <b>{track.name}</b>{get_time_elapsed_str(track)}"
        for track in played_tracks
    )
    await message.reply("\n".join(formatted_tracks), disable_web_page_preview=True)
