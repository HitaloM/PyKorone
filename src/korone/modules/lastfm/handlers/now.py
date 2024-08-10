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
    format_tags,
    get_biggest_lastfm_image,
    get_time_elapsed_str,
    name_with_link,
)
from korone.utils.i18n import gettext as _


class LastFMPlayingHandler(MessageHandler):
    @staticmethod
    @router.message(Command(commands=["lfm", "lastfm", "lmu"]))
    async def handle(client: Client, message: Message) -> None:
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
            last_played = (await last_fm.get_recent_tracks(last_fm_user, limit=1))[0]
            track_info = await last_fm.get_track_info(
                last_played.artist.name, last_played.name, last_fm_user
            )
        except LastFMError as e:
            if "user not found" in e.message.lower():
                await message.reply(_("Your LastFM username was not found! Try setting it again."))
                return
            raise
        except IndexError:
            await message.reply(_("No recent tracks found for your LastFM account."))
            return

        user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)

        if last_played.now_playing:
            text = _("{user}'s is listening to:\n").format(user=user_link)
        else:
            text = _("{user}'s was listening to:\n").format(user=user_link)

        text += "🎧 <i>{track_artist}</i> — <b>{track_name}</b>{loved}{time}{plays}".format(
            track_artist=last_played.artist.name,
            track_name=last_played.name,
            loved=_(", ❤️ loved") if last_played.loved else "",
            time="" if last_played.now_playing else get_time_elapsed_str(last_played),
            plays=_(" ∙ <code>{track_playcount} plays</code>").format(
                track_playcount=track_info.playcount
            )
            if track_info.playcount > 0
            else "",
        )

        if track_info.tags:
            text += f"\n\n{format_tags(track_info)}"

        if image := await get_biggest_lastfm_image(last_played):
            await message.reply_photo(photo=image, caption=text)
            return

        await message.reply(text, disable_web_page_preview=True)
