from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    TimePeriod,
    check_compatibility_users,
    fetch_lastfm_users,
    handle_lastfm_error,
    parse_collage_arg,
    period_to_str,
)
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import User

    from korone.modules.lastfm.utils import LastFMArtist


@flags.help(description=l_("Checks compatibility between two Last.fm users."))
@flags.disableable(name="lfmcompat")
class LastFMCompatHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("lfmcompat"),)

    async def handle(self) -> None:
        if not self.event.reply_to_message:
            await self.event.reply(_("Reply to a message to get the compatibility!"))
            return

        user1 = self.event.from_user
        user2 = self.event.reply_to_message.from_user

        if not user1 or not user2:
            await self.event.reply(_("Could not identify both users."))
            return

        if not await check_compatibility_users(self.event, user1, user2):
            return

        user1_db, user2_db = await fetch_lastfm_users(self.event, user1.id, user2.id)
        if not user1_db or not user2_db:
            return

        _collage_size, period, _entry_type, _no_text = parse_collage_arg(
            getattr(self.data.get("command"), "args", None), default_period=TimePeriod.OneYear
        )
        last_fm = LastFMClient()

        try:
            artists1 = await last_fm.get_top_artists(user1_db, period, limit=200)
            artists2 = await last_fm.get_top_artists(user2_db, period, limit=200)
        except LastFMError as exc:
            await handle_lastfm_error(self.event, exc)
            return

        if not artists1 or not artists2:
            await self.event.reply(_("No top artists found for your Last.fm account."))
            return

        score, mutual = calculate_compatibility(artists1, artists2)
        await self.event.reply(format_compatibility_response(user1, user2, mutual, score, period))


def calculate_compatibility(artists1: list[LastFMArtist], artists2: list[LastFMArtist]) -> tuple[int, list[str]]:
    denominator = min(len(artists1), len(artists2), 40)
    if denominator <= 2:
        return 0, []

    artists2_names = {artist.name for artist in artists2}
    mutual = [artist.name for artist in artists1 if artist.name in artists2_names][:8]
    numerator = sum(1 for artist in artists1 if artist.name in artists2_names)

    score = (numerator * 100) // denominator
    score = min(score, 100)

    return score, mutual


def format_compatibility_response(user1: User, user2: User, mutual: list[str], score: int, period: TimePeriod) -> str:
    if not mutual or score == 0:
        return _("No common artists in {period}").format(period=period_to_str(period))

    return _("{user1} and {user2} listen to {mutual}...\n\nCompatibility score is {score}%, based on {period}").format(
        user1=user1.mention_html(),
        user2=user2.mention_html(),
        mutual=", ".join(mutual),
        score=score,
        period=period_to_str(period),
    )
