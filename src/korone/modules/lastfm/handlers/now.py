# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import LastFMClient
from korone.modules.utils.filters import Command
from korone.utils.i18n import gettext as _


class NowPlayingHandler(MessageHandler):
    @staticmethod
    @router.message(Command(commands=["now", "status", "np", "lmu", "lt"]))
    async def handle(client: Client, message: Message) -> None:
        last_fm = LastFMClient()

        last_fm_user = await get_lastfm_user(message.from_user.id)
        if not last_fm_user:
            await message.reply("You need to set your LastFM username first!")
            return

        last_played = (await last_fm.get_recent_tracks(last_fm_user, limit=1))[0]
        track_info = await last_fm.get_track_info(
            last_played.artist, last_played.name, last_fm_user
        )

        user_mention = message.from_user.mention()

        if last_played.now_playing:
            text = _("{user}'s is listening:").format(user=user_mention)
        else:
            text = _("{user}'s was listening:").format(user=user_mention)

        text += _("\n\n<b>{track_name}</b> {loved}{plays}").format(
            track_name=track_info.name,
            loved="❤️" if track_info.loved else "",
            plays=_(" - <code>{track_playcount} plays</code>").format(
                track_playcount=track_info.playcount
            )
            if track_info.playcount > 0
            else "",
        )

        text += _("\n<b>By:</b> <i>{track_artist}</i>").format(track_artist=track_info.artist)

        images = last_played.images
        image = next((img for img in images if img.size == "extralarge"), None)

        if image:
            await message.reply_photo(photo=image.url, caption=text)
            return

        await message.reply(text)
