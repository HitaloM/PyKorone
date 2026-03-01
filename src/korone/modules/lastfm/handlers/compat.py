from __future__ import annotations

from typing import TYPE_CHECKING, Any, override
from urllib.parse import quote_plus

from aiogram import flags
from aiogram.enums import ChatAction
from aiogram.filters import Command
from ass_tg.types import OptionalArg, WordArg
from stfu_tg import Code, Template, Url

from korone.db.repositories.lastfm import LastFMRepository
from korone.modules.lastfm.handlers.base import LastFMHandlerSupport
from korone.modules.lastfm.utils import LastFMClient, LastFMError, format_lastfm_error
from korone.modules.lastfm.utils.periods import LastFMPeriod, parse_period_token, period_label
from korone.modules.utils_.message import is_real_reply
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


COMPAT_MUTUAL_ARTISTS_LIMIT = 8
COMPAT_DENOMINATOR_LIMIT = 40


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
        username_a: str,
        username_b: str,
        mutual_artists: list[str],
        common_artists_total: int,
        score: int,
        period: LastFMPeriod,
    ) -> str:
        return str(
            Template(
                _("{user_a} and {user_b} listen to {artists}\n\nCompatibility score is {score}%, based on {period}"),
                user_a=Url(username_a, cls.build_profile_url(username_a)),
                user_b=Url(username_b, cls.build_profile_url(username_b)),
                artists=cls.build_artists_preview(mutual_artists, common_artists_total=common_artists_total),
                score=max(0, min(score, 100)),
                period=period_label(period),
            )
        )

    @classmethod
    def no_common_message(cls, period: LastFMPeriod) -> str:
        return _("No common artists in {period}.").format(period=period_label(period))


@flags.help(description=l_("Show Last.fm compatibility with the replied user."))
@flags.chat_action(action=ChatAction.TYPING, initial_sleep=0.7)
@flags.disableable(name="lfmcompat")
class LastFMCompatHandler(LastFMCompatFormatter, KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"period": OptionalArg(WordArg(l_("Period")))}

    @staticmethod
    @override
    def filters() -> tuple[CallbackType, ...]:
        return (Command("lfmcompat", "lcompat"),)

    @override
    async def handle(self) -> None:
        if not self.event.from_user:
            await self.event.reply(_("Could not identify your Telegram user."))
            return

        if (
            not self.event.reply_to_message
            or not is_real_reply(self.event)
            or not self.event.reply_to_message.from_user
        ):
            await self.event.reply(
                str(
                    Template(
                        _("Usage: {example}. Reply to someone's message in a group."), example=Code("/lfmcompat 1y")
                    )
                )
            )
            return

        source_user = self.event.from_user
        target_user = self.event.reply_to_message.from_user

        if source_user.id == target_user.id:
            await self.event.reply(_("Lookie, it's me!!!"))
            return

        if source_user.is_bot or target_user.is_bot:
            await self.event.reply(_("Bots don't listen to music."))
            return

        source_username = await LastFMRepository.get_username(source_user.id)
        if not source_username:
            await self.event.reply(self.missing_username_text())
            return

        target_username = await LastFMRepository.get_username(target_user.id)
        if not target_username:
            await self.event.reply(_("This user needs to set Last.fm first with /setlfm."))
            return

        period = parse_period_token(str(self.data.get("period") or "").strip(), default=LastFMPeriod.ONE_YEAR)

        try:
            client = LastFMClient()
            artists_a = await client.get_top_artists(username=source_username, period=period.value, limit=100)
            artists_b = await client.get_top_artists(username=target_username, period=period.value, limit=100)
        except LastFMError as exc:
            await self.event.reply(format_lastfm_error(exc))
            return

        denominator = min(len(artists_a), len(artists_b), COMPAT_DENOMINATOR_LIMIT)
        if denominator <= 2:
            await self.event.reply(self.no_common_message(period))
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
            await self.event.reply(self.no_common_message(period))
            return

        await self.event.reply(
            self.format_result(
                username_a=source_username,
                username_b=target_username,
                mutual_artists=mutual_artists,
                common_artists_total=numerator,
                score=score,
                period=period,
            )
        )
