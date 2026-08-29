from dataclasses import dataclass
from typing import TYPE_CHECKING, override
from urllib.parse import quote_plus

from aiogram import flags
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import User

from korone.args import ArgumentSchema
from korone.db.repositories.lastfm import LastFMRepository
from korone.modules.lastfm.args import LastFMPeriodArg
from korone.modules.lastfm.handlers.base import LastFMHandlerSupport, LastFMUserContext
from korone.modules.lastfm.utils import LastFMClient, LastFMError, format_lastfm_error
from korone.modules.lastfm.utils.periods import LastFMPeriod, period_label
from korone.modules.utils_.get_user import get_arg_or_reply_user
from korone.ui import Code, MessageContent, link, template
from korone.utils.exception import KoroneError
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


COMPAT_MUTUAL_ARTISTS_LIMIT = 8
COMPAT_DENOMINATOR_LIMIT = 40


@dataclass(frozen=True, slots=True)
class LastFMCompatArguments:
    period: LastFMPeriod = LastFMPeriod.ONE_YEAR


class LastFMCompatFormatter(LastFMHandlerSupport):
    @staticmethod
    def build_profile_url(username: str) -> str:
        return f"https://www.last.fm/user/{quote_plus(username)}"

    @staticmethod
    def build_artists_preview(mutual_artists: list[str], *, common_artists_total: int) -> str:
        artists = ", ".join(mutual_artists)
        if common_artists_total > len(mutual_artists):
            return f"{artists}..."
        return artists

    @classmethod
    def format_result(
        cls,
        *,
        user_a: LastFMUserContext,
        user_b: LastFMUserContext,
        mutual_artists: list[str],
        common_artists_total: int,
        score: int,
        period: LastFMPeriod,
    ) -> MessageContent:
        return template(
            _("{user_a} and {user_b} listen to {artists}\n\nCompatibility score is {score}%, based on {period}"),
            user_a=link(user_a.display_name, cls.build_profile_url(user_a.username)),
            user_b=link(user_b.display_name, cls.build_profile_url(user_b.username)),
            artists=cls.build_artists_preview(mutual_artists, common_artists_total=common_artists_total),
            score=max(0, min(score, 100)),
            period=period_label(period),
        )

    @classmethod
    def no_common_message(cls, period: LastFMPeriod) -> MessageContent:
        return template(_("No common artists in {period}."), period=period_label(period))


@flags.help(
    description=l_("Show Last.fm compatibility with the replied user. Supported periods: all, 1y, 6m, 3m, 1m, 7d."),
    examples=(
        (l_("Compare last year (reply to user)"), "1y"),
        (l_("Compare last week (reply to user)"), "7day"),
        (l_("Compare all-time (reply to user)"), "all"),
    ),
)
@flags.chat_action(action=ChatAction.TYPING, initial_sleep=0.7)
@flags.disableable(name="lfmcompat")
class LastFMCompatHandler(LastFMCompatFormatter, KoroneMessageHandler[LastFMCompatArguments]):
    arguments = ArgumentSchema(LastFMCompatArguments, period=LastFMPeriodArg(l_("Period")))

    @classmethod
    @override
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("lfmcompat", "lcompat"),)

    @override
    async def handle(self) -> None:
        if not self.event.from_user:
            await self.event.reply(_("Could not identify your Telegram user."))
            return

        try:
            target_candidate = get_arg_or_reply_user(self.event, None)
        except KoroneError:
            target_candidate = None

        if not isinstance(target_candidate, User):
            await self.answer(
                template(_("Usage: {example}. Reply to someone's message in a group."), example=Code("/lfmcompat 1y"))
            )
            return

        source_user = self.event.from_user
        target_user = target_candidate

        if source_user.id == target_user.id:
            await self.event.reply(_("Lookie, it's me!!!"))
            return

        if source_user.is_bot or target_user.is_bot:
            await self.event.reply(_("Bots don't listen to music."))
            return

        source_username = await LastFMRepository.get_username(source_user.id)
        if not source_username:
            await type(self).reply_missing_username(self.event)
            return

        target_username = await LastFMRepository.get_username(target_user.id)
        if not target_username:
            await self.event.reply(_("This user needs to set Last.fm first with /setlfm."))
            return

        source_context = LastFMUserContext(
            username=source_username, display_name=source_user.first_name, telegram_user_id=source_user.id
        )
        target_context = LastFMUserContext(
            username=target_username, display_name=target_user.first_name, telegram_user_id=target_user.id
        )
        period = self.args.period

        try:
            client = LastFMClient()
            artists_a = await client.get_top_artists(username=source_username, period=period.value, limit=100)
            artists_b = await client.get_top_artists(username=target_username, period=period.value, limit=100)
        except LastFMError as exc:
            await self.event.reply(format_lastfm_error(exc))
            return

        denominator = min(len(artists_a), len(artists_b), COMPAT_DENOMINATOR_LIMIT)
        if denominator <= 2:
            await self.answer(self.no_common_message(period))
            return

        artists_b_names = {artist.name for artist in artists_b}
        mutual_artists: list[str] = []
        numerator = 0

        for artist in artists_a:
            if artist.name not in artists_b_names:
                continue

            numerator += 1
            if len(mutual_artists) < COMPAT_MUTUAL_ARTISTS_LIMIT:
                mutual_artists.append(artist.name)

        score = min(numerator * 100 // denominator, 100) if denominator > 2 else 0
        if not mutual_artists or score == 0:
            await self.answer(self.no_common_message(period))
            return

        await self.answer(
            self.format_result(
                user_a=source_context,
                user_b=target_context,
                mutual_artists=mutual_artists,
                common_artists_total=numerator,
                score=score,
                period=period,
            )
        )
