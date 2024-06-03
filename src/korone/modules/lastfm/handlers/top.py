# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import (
    EntryType,
    LastFMClient,
    LastFMError,
    LastFMTrack,
    TimePeriod,
    parse_collage_arg,
    period_to_str,
)
from korone.modules.utils.filters import Command, CommandObject
from korone.utils.i18n import gettext as _


class LastFMTopHandler(MessageHandler):
    @staticmethod
    def entry_type_to_str(entry_type: EntryType) -> str:
        if entry_type == EntryType.Artist:
            return _("artists")
        if entry_type == EntryType.Track:
            return _("tracks")
        return _("albums")

    @router.message(Command(commands=["lfmt", "top"]))
    async def handle(self, client: Client, message: Message) -> None:
        last_fm_user = await get_lastfm_user(message.from_user.id)
        if not last_fm_user:
            await message.reply(_("You need to set your LastFM username first!"))
            return

        command = CommandObject(message).parse()
        args = command.args

        period = TimePeriod.AllTime
        entry_type = EntryType.Artist

        if args:
            __, period, entry_type, __ = parse_collage_arg(args, entry_type)
            if not entry_type:
                await message.reply(
                    _("Invalid entry type! Use one of the following: artist, track, album")
                )
                return

        last_fm = LastFMClient()

        try:
            if entry_type == EntryType.Artist:
                top_items = await last_fm.get_top_artists(
                    last_fm_user, period=period.value, limit=5
                )
            elif entry_type == EntryType.Track:
                top_items = await last_fm.get_top_tracks(
                    last_fm_user, period=period.value, limit=5
                )
            else:
                top_items = await last_fm.get_top_albums(
                    last_fm_user, period=period.value, limit=5
                )
        except LastFMError as e:
            error_message = str(e)
            if error_message == "User not found":
                await message.reply(_("Your LastFM username was not found! Try setting it again."))
            else:
                await message.reply(
                    _(
                        "An error occurred while fetching your LastFM data!\n"
                        "Error: <i>{error}</i>"
                    ).format(error=error_message)
                )
            return

        user_mention = message.from_user.mention()

        text = _("{user}'s top 5 {entry} for {period}:\n\n").format(
            user=user_mention,
            entry=self.entry_type_to_str(entry_type),
            period=period_to_str(period),
        )
        for item in top_items:
            if isinstance(item, LastFMTrack):
                text += f"{item.artist} — {item.name}"
            else:
                text += item.name

            text += _(" -> {scrobbles} plays\n").format(scrobbles=item.playcount)

        await message.reply(text)
