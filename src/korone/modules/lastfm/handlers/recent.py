# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    LastFMTrack,
    get_time_elapsed_str,
)
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

    recent_tracks = await fetch_recent_tracks(last_fm, last_fm_user, message)
    if recent_tracks is None:
        return

    last_played, played_tracks = process_recent_tracks(recent_tracks)

    user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)
    text = format_recent_plays(last_played, played_tracks, user_link)

    await message.reply(text, disable_web_page_preview=True)


async def fetch_recent_tracks(
    last_fm: LastFMClient, last_fm_user: str, message: Message
) -> list[LastFMTrack] | None:
    try:
        return await last_fm.get_recent_tracks(last_fm_user, limit=6)
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


def process_recent_tracks(
    recent_tracks: list[LastFMTrack],
) -> tuple[LastFMTrack | None, list[LastFMTrack]]:
    if not recent_tracks:
        return None, []

    last_played = recent_tracks[0]
    played_tracks = recent_tracks[1:6] if last_played.now_playing else recent_tracks[:5]
    return last_played, played_tracks


def format_recent_plays(
    last_played: LastFMTrack | None, played_tracks: list[LastFMTrack], user_link: str
) -> str:
    formatted_tracks = []

    if last_played and last_played.now_playing:
        formatted_tracks.extend((
            _("{user}'s is listening to:\n").format(user=user_link)
            + format_track(last_played, now_playing=True),
            _("\nLast 5 plays:"),
        ))
    else:
        formatted_tracks.append(_("{user}'s was listening to:\n").format(user=user_link))

    formatted_tracks.extend(format_track(track) for track in played_tracks)

    return "\n".join(formatted_tracks)


def format_track(track: LastFMTrack, now_playing: bool = False) -> str:
    time_elapsed_str = "" if now_playing else get_time_elapsed_str(track)
    return f"🎧 <i>{track.artist.name}</i> — <b>{track.name}</b>{time_elapsed_str}"
