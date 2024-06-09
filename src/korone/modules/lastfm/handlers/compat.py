# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    TimePeriod,
    parse_collage_arg,
    period_to_str,
)
from korone.utils.i18n import gettext as _


class LastFMCompatHandler(MessageHandler):
    @router.message(Command(commands=["lfmcomp", "compat"]))
    async def handle(self, client: Client, message: Message) -> None:
        if not message.reply_to_message:
            await message.reply(_("Reply to a message to get the compatibility!"))
            return

        user1 = message.from_user
        user1_db = await get_lastfm_user(user1.id)
        if not user1_db:
            await message.reply(_("You need to set your LastFM username first!"))
            return

        user2 = message.reply_to_message.from_user
        if user1.id == user2.id:
            await message.reply(_("You can't get the compatibility with yourself!"))
            return

        if user1.is_bot or user2.is_bot:
            await message.reply(_("Bots won't have music taste!"))
            return

        user2_db = await get_lastfm_user(user2.id)
        if not user2_db:
            await message.reply(_("The user you replied to doesn't have a LastFM account linked!"))
            return

        command = CommandObject(message).parse()
        _collage_size, period, _entry_type, _no_text = parse_collage_arg(
            command.args, default_period=TimePeriod.OneYear
        )
        last_fm = LastFMClient()

        try:
            artists1 = await last_fm.get_top_artists(user1_db, period.value, limit=200)
            artists2 = await last_fm.get_top_artists(user2_db, period.value, limit=200)
        except LastFMError as e:
            await self.handle_lastfm_error(e, message)
            return

        text = self.calculate_compatibility_text(user1, user2, artists1, artists2, period)
        await message.reply(text)

    @staticmethod
    async def handle_lastfm_error(error: LastFMError, message: Message) -> None:
        error_message = str(error)
        if error_message == "User not found":
            await message.reply(_("Your LastFM username was not found! Try setting it again."))
        else:
            await message.reply(
                _(
                    "An error occurred while fetching your LastFM data!\nError: <i>{error}</i>"
                ).format(error=error_message)
            )

    @staticmethod
    def calculate_compatibility_text(user1, user2, artists1, artists2, period) -> str:
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
