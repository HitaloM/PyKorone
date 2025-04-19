# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html

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
    handle_lastfm_error,
    name_with_link,
    parse_collage_arg,
    period_to_str,
)
from korone.utils.i18n import gettext as _


@router.message(Command("lfmtop"))
async def lfmtop_command(client: Client, message: Message) -> None:
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
        top_items = await fetch_top_items(last_fm, last_fm_user, entry_type, period)
    except LastFMError as e:
        await handle_lastfm_error(message, e)
        return

    if not top_items:
        await message.reply(_("No top items found."))
        return

    user_link = name_with_link(
        name=html.escape(str(message.from_user.first_name)), username=last_fm_user
    )

    text = format_top_items_response(user_link, top_items, entry_type, period)
    await message.reply(text, disable_web_page_preview=True)


async def fetch_top_items(
    last_fm: LastFMClient, username: str, entry_type: EntryType, period: TimePeriod
) -> list:
    match entry_type:
        case EntryType.Artist:
            return await last_fm.get_top_artists(username, period=period, limit=5)
        case EntryType.Track:
            return await last_fm.get_top_tracks(username, period=period, limit=5)
        case EntryType.Album:
            return await last_fm.get_top_albums(username, period=period, limit=5)


def format_top_items_response(
    user_link: str, top_items: list, entry_type: EntryType, period: TimePeriod
) -> str:
    entry_name = {
        EntryType.Artist: _("artists"),
        EntryType.Track: _("tracks"),
        EntryType.Album: _("albums"),
    }[entry_type]

    text = _("{user}'s top 5 {entry} for {period}:\n\n").format(
        user=user_link, entry=entry_name, period=period_to_str(period)
    )

    for item in top_items:
        if isinstance(item, LastFMTrack):
            text += f"{html.escape(item.artist.name)} — {html.escape(item.name)}"
        else:
            text += html.escape(item.name)
        text += _(" -> {scrobbles} plays\n").format(scrobbles=item.playcount)

    return text
