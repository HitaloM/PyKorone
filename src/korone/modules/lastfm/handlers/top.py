# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
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


@router.message(Command("lfmtop"))
async def lfmtop_command(client: Client, message: Message) -> None:
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
    period, entry_type = parse_command_args(command)

    if not entry_type:
        await message.reply(
            _("Invalid entry type! Use one of the following: artist, track, album")
        )
        return

    last_fm = LastFMClient()

    top_items = await fetch_top_items(last_fm, last_fm_user, entry_type, period, message)
    if not top_items:
        return

    user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)
    text = format_top_items_text(user_link, top_items, entry_type, period)

    await message.reply(text, disable_web_page_preview=True)


def parse_command_args(command: CommandObject) -> tuple[TimePeriod, EntryType]:
    period = TimePeriod.AllTime
    entry_type = EntryType.Artist

    if args := command.args:
        _collage_size, period, entry_type, _no_text = parse_collage_arg(
            args, default_entry=entry_type
        )

    return period, entry_type


async def fetch_top_items(
    last_fm: LastFMClient,
    last_fm_user: str,
    entry_type: EntryType,
    period: TimePeriod,
    message: Message,
) -> list | None:
    try:
        return await get_top_items(last_fm, last_fm_user, entry_type, period)
    except LastFMError as e:
        await handle_lastfm_error(e, message)
        return None


async def get_top_items(
    last_fm: LastFMClient, last_fm_user: str, entry_type: EntryType, period: TimePeriod
) -> list:
    match entry_type:
        case EntryType.Artist:
            return await last_fm.get_top_artists(last_fm_user, period=period, limit=5)
        case EntryType.Track:
            return await last_fm.get_top_tracks(last_fm_user, period=period, limit=5)
        case EntryType.Album:
            return await last_fm.get_top_albums(last_fm_user, period=period, limit=5)


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


def format_top_items_text(
    user_link: str, top_items: list, entry_type: EntryType, period: TimePeriod
) -> str:
    text = _("{user}'s top 5 {entry} for {period}:\n\n").format(
        user=user_link,
        entry=entry_type_to_str(entry_type),
        period=period_to_str(period),
    )
    for item in top_items:
        if isinstance(item, LastFMTrack):
            text += f"{item.artist.name} — {item.name}"
        else:
            text += item.name

        text += _(" -> {scrobbles} plays\n").format(scrobbles=item.playcount)

    return text


def entry_type_to_str(entry_type: EntryType) -> str:
    if entry_type == EntryType.Artist:
        return _("artists")
    return _("tracks") if entry_type == EntryType.Track else _("albums")
