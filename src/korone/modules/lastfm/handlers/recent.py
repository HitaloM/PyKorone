# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>


from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.handlers.abstract import MessageHandler
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    LastFMTrack,
    get_time_elapsed_str,
)
from korone.modules.lastfm.utils.formatters import name_with_link
from korone.utils.i18n import gettext as _


class LastFMRecentsHandler(MessageHandler):
    @router.message(Command(commands=["lfmr", "recent"]))
    async def handle(self, client: Client, message: Message) -> None:
        last_fm_user = await get_lastfm_user(message.from_user.id)
        if not last_fm_user:
            await message.reply(_("You need to set your LastFM username first!"))
            return

        last_fm = LastFMClient()

        try:
            recent_tracks = await last_fm.get_recent_tracks(last_fm_user, limit=6)
        except LastFMError as e:
            error_message = str(e)
            if error_message == "User not found":
                await message.reply(_("Your LastFM username was not found! Try setting it again."))
            else:
                await message.reply(
                    _(
                        "An error occurred while fetching your LastFM data!\nError: <i>{error}</i>"
                    ).format(error=error_message)
                )
            return

        if recent_tracks:
            last_played = recent_tracks[0]
            played_tracks = recent_tracks[1:6] if last_played.now_playing else recent_tracks[0:5]
        else:
            last_played = None
            played_tracks = []

        user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)

        text = self.format_recent_plays(last_played, played_tracks, user_link)
        await message.reply(text, disable_web_page_preview=True)

    def format_recent_plays(
        self, last_played: LastFMTrack | None, played_tracks: list[LastFMTrack], user_link: str
    ) -> str:
        formatted_tracks = []

        if last_played and last_played.now_playing:
            formatted_tracks.extend((
                _("{user}'s is listening to:\n").format(user=user_link)
                + self.format_track(last_played, now_playing=True),
                _("\nLast 5 plays:"),
            ))
        else:
            formatted_tracks.append(_("{user}'s was listening to:\n").format(user=user_link))

        formatted_tracks.extend(self.format_track(track) for track in played_tracks)

        return "\n".join(formatted_tracks)

    @staticmethod
    def format_track(track: LastFMTrack, now_playing: bool = False) -> str:
        time_elapsed_str = "" if now_playing else get_time_elapsed_str(track)

        return _("🎧 <i>{track.artist}</i> — <b>{track.name}</b>{time}").format(
            track=track, time=time_elapsed_str
        )
