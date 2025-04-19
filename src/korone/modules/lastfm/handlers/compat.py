# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.lastfm.utils import (
    LastFMArtist,
    LastFMClient,
    LastFMError,
    TimePeriod,
    check_compatibility_users,
    fetch_lastfm_users,
    handle_lastfm_error,
    parse_collage_arg,
    period_to_str,
)
from korone.utils.i18n import gettext as _


@router.message(Command("lfmcompat"))
async def lfmcompat_command(client: Client, message: Message) -> None:
    if not message.reply_to_message:
        await message.reply(_("Reply to a message to get the compatibility!"))
        return

    user1, user2 = message.from_user, message.reply_to_message.from_user

    if not await check_compatibility_users(message, user1, user2):
        return

    user1_db, user2_db = await fetch_lastfm_users(message, user1.id, user2.id)
    if not user1_db or not user2_db:
        return

    command = CommandObject(message).parse()
    _collage_size, period, _entry_type, _no_text = parse_collage_arg(
        command.args, default_period=TimePeriod.OneYear
    )
    last_fm = LastFMClient()

    try:
        artists1 = await last_fm.get_top_artists(user1_db, period, limit=200)
        artists2 = await last_fm.get_top_artists(user2_db, period, limit=200)
    except LastFMError as e:
        await handle_lastfm_error(message, e)
        return

    if not artists1 or not artists2:
        await message.reply(_("No top artists found for your LastFM account."))
        return

    score, mutual = calculate_compatibility(artists1, artists2)
    await message.reply(format_compatibility_response(user1, user2, mutual, score, period))


def calculate_compatibility(
    artists1: list[LastFMArtist], artists2: list[LastFMArtist]
) -> tuple[int, list[str]]:
    numerator = 0
    mutual = []
    denominator = min(len(artists1), len(artists2), 40)

    for artist1 in artists1:
        for artist2 in artists2:
            if artist1.name == artist2.name:
                numerator += 1
                if len(mutual) < 8:
                    mutual.append(artist1.name)
                break

    score = (numerator * 100) // denominator if denominator > 2 else 0
    score = min(score, 100)

    return score, mutual


def format_compatibility_response(
    user1, user2, mutual: list[str], score: int, period: TimePeriod
) -> str:
    if not mutual or score == 0:
        return _("No common artists in {period}").format(period=period_to_str(period))

    return _(
        "{user1} and {user2} listen to {mutual}...\n\n"
        "Compatibility score is {score}%, based on {period}"
    ).format(
        user1=user1.mention(),
        user2=user2.mention(),
        mutual=", ".join(mutual),
        score=score,
        period=period_to_str(period),
    )
