from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import flags
from ass_tg.types import OptionalArg, TextArg
from stfu_tg import PreformattedHTML, Template

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import (
    EntryType,
    LastFMClient,
    LastFMError,
    LastFMTrack,
    TimePeriod,
    get_lastfm_user_or_reply,
    get_user_link,
    handle_lastfm_error,
    parse_collage_arg,
    period_to_str,
)
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


@flags.help(description=l_("Shows your top artists, tracks, or albums from Last.fm."))
@flags.disableable(name="lfmtop")
class LastFMTopHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"args": OptionalArg(TextArg(l_("Args")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("lfmtop"),)

    async def handle(self) -> None:
        last_fm_user = await get_lastfm_user_or_reply(self.event)
        if not last_fm_user:
            return

        args = (self.data.get("args") or "").strip()
        period = TimePeriod.AllTime
        entry_type = EntryType.Artist

        if args:
            _collage_size, period, entry_type, _no_text = parse_collage_arg(args, default_entry=entry_type)

        if not entry_type:
            await self.event.reply(_("Invalid entry type! Use one of the following: artist, track, album"))
            return

        last_fm = LastFMClient()
        try:
            top_items = await fetch_top_items(last_fm, last_fm_user, entry_type, period)
        except LastFMError as exc:
            await handle_lastfm_error(self.event, exc)
            return

        if not top_items:
            await self.event.reply(_("No top items found."))
            return

        user_link = get_user_link(self.event, last_fm_user)
        text = format_top_items_response(user_link, top_items, entry_type, period)
        await self.event.reply(text, disable_web_page_preview=True)


async def fetch_top_items(last_fm: LastFMClient, username: str, entry_type: EntryType, period: TimePeriod) -> list:
    match entry_type:
        case EntryType.Artist:
            return await last_fm.get_top_artists(username, period=period, limit=5)
        case EntryType.Track:
            return await last_fm.get_top_tracks(username, period=period, limit=5)
        case EntryType.Album:
            return await last_fm.get_top_albums(username, period=period, limit=5)


def format_top_items_response(user_link: str, top_items: list, entry_type: EntryType, period: TimePeriod) -> str:
    entry_name = {EntryType.Artist: _("artists"), EntryType.Track: _("tracks"), EntryType.Album: _("albums")}[
        entry_type
    ]

    text = Template(
        _("{user}'s top 5 {entry} for {period}:\n\n"),
        user=PreformattedHTML(user_link),
        entry=entry_name,
        period=period_to_str(period),
    ).to_html()

    for item in top_items:
        if isinstance(item, LastFMTrack):
            item_name: str | Template = Template("{artist} — {track}", artist=item.artist.name, track=item.name)
        else:
            item_name = str(item.name)

        text += Template(
            _("{entry_text} -> {scrobbles} plays\n"), entry_text=item_name, scrobbles=item.playcount
        ).to_html()

    return text
