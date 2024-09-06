# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.lastfm.utils import (
    EntryType,
    LastFMClient,
    LastFMError,
    LastFMTrack,
    TimePeriod,
    get_lastfm_user_or_reply,
    name_with_link,
    parse_collage_arg,
    period_to_str,
)
from korone.utils.i18n import gettext as _


@router.message(Command("lfmtop"))
async def lfmtop_command(client: Client, message: Message) -> None:  # noqa: C901
    last_fm_user = await get_lastfm_user_or_reply(message)
    if not last_fm_user:
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
        match entry_type:
            case EntryType.Artist:
                top_items = await last_fm.get_top_artists(last_fm_user, period=period, limit=5)
            case EntryType.Track:
                top_items = await last_fm.get_top_tracks(last_fm_user, period=period, limit=5)
            case EntryType.Album:
                top_items = await last_fm.get_top_albums(last_fm_user, period=period, limit=5)
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

    if not top_items:
        await message.reply(_("No top items found."))
        return

    user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)
    text = _("{user}'s top 5 {entry} for {period}:\n\n").format(
        user=user_link,
        entry=_("artists")
        if entry_type == EntryType.Artist
        else _("tracks")
        if entry_type == EntryType.Track
        else _("albums"),
        period=period_to_str(period),
    )

    for item in top_items:
        if isinstance(item, LastFMTrack):
            text += f"{item.artist.name} — {item.name}"
        else:
            text += item.name
        text += _(" -> {scrobbles} plays\n").format(scrobbles=item.playcount)

    await message.reply(text, disable_web_page_preview=True)
