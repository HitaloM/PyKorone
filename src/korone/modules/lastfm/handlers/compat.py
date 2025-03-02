# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>


from hydrogram import Client
from hydrogram.types import Message, User

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils.commons import handle_lastfm_error
from korone.modules.lastfm.utils.errors import LastFMError
from korone.modules.lastfm.utils.formatters import period_to_str
from korone.modules.lastfm.utils.lastfm_api import LastFMClient, TimePeriod
from korone.modules.lastfm.utils.parse_collage import parse_collage_arg
from korone.modules.lastfm.utils.types import LastFMArtist
from korone.utils.i18n import gettext as _


@router.message(Command("lfmcompat"))
async def lfmcompat_command(client: Client, message: Message) -> None:
    if not message.reply_to_message:
        await message.reply(_("Reply to a message to get the compatibility!"))
        return

    user1, user2 = message.from_user, message.reply_to_message.from_user

    if not await check_users(message, user1, user2):
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

    score, mutual = calculate_compatibility(artists1, artists2, period)
    await message.reply(format_reply(user1, user2, mutual, score, period))


async def check_users(message: Message, user1: User, user2: User) -> bool:
    if user1.id == user2.id:
        await message.reply(_("You can't get the compatibility with yourself!"))
        return False

    if user1.is_bot or user2.is_bot:
        await message.reply(_("Bots won't have music taste!"))
        return False

    return True


async def fetch_lastfm_users(
    message: Message, user1_id: int, user2_id: int
) -> tuple[str | None, str | None]:
    user1_db = await get_lastfm_user(user1_id)
    user2_db = await get_lastfm_user(user2_id)

    if not user1_db:
        await message.reply(
            _(
                "You need to set your LastFM username first! "
                "Example: <code>/setlfm username</code>."
            )
        )

    if not user2_db:
        await message.reply(
            _(
                "The user you replied to doesn't have a LastFM account linked! "
                "Hint them to set it using <code>/setlfm username</code>."
            )
        )

    return user1_db, user2_db


def calculate_compatibility(
    artists1: list[LastFMArtist], artists2: list[LastFMArtist], period: TimePeriod
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


def format_reply(
    user1: User, user2: User, mutual: list[str], score: int, period: TimePeriod
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
