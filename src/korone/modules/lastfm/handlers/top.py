# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import (
    EntryType,
    LastFMClient,
    LastFMError,
    LastFMTrack,
    TimePeriod,
    name_with_link,
    parse_collage_arg,
    period_to_str,
)
from korone.utils.i18n import gettext as _


class LastFMTopHandler(MessageHandler):
    @router.message(Command("lfmtop"))
    async def handle(self, client: Client, message: Message) -> None:
        last_fm_user = await get_lastfm_user(message.from_user.id)
        if not last_fm_user:
            await message.reply(
                _(
                    "You need to set your LastFM username first! "
                    "Example: <code>/setlfm username</code>."
                )
            )
            return

        command = CommandObject(message).parse()
        period = TimePeriod.AllTime
        entry_type = EntryType.Artist

        if args := command.args:
            _collage_size, period, entry_type, _no_text = parse_collage_arg(
                args, default_entry=entry_type
            )
            if not entry_type:
                await message.reply(
                    _("Invalid entry type! Use one of the following: artist, track, album")
                )
                return

        last_fm = LastFMClient()

        try:
            if entry_type == EntryType.Artist:
                top_items = await last_fm.get_top_artists(last_fm_user, period=period, limit=5)
            elif entry_type == EntryType.Track:
                top_items = await last_fm.get_top_tracks(last_fm_user, period=period, limit=5)
            else:
                top_items = await last_fm.get_top_albums(last_fm_user, period=period, limit=5)
        except LastFMError as e:
            if "user not found" in e.message.lower():
                await message.reply(_("Your LastFM username was not found! Try setting it again."))
            else:
                await message.reply(
                    _(
                        "An error occurred while fetching your LastFM data!"
                        "\n<blockquote>{error}</blockquote>"
                    ).format(error=e.message)
                )
                return

        user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)

        text = _("{user}'s top 5 {entry} for {period}:\n\n").format(
            user=user_link,
            entry=self.entry_type_to_str(entry_type),
            period=period_to_str(period),
        )
        for item in top_items:
            if isinstance(item, LastFMTrack):
                text += f"{item.artist.name} — {item.name}"
            else:
                text += item.name

            text += _(" -> {scrobbles} plays\n").format(scrobbles=item.playcount)

        await message.reply(text, disable_web_page_preview=True)

    @staticmethod
    def entry_type_to_str(entry_type: EntryType) -> str:
        if entry_type == EntryType.Artist:
            return _("artists")
        return _("tracks") if entry_type == EntryType.Track else _("albums")
