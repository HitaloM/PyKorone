from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from aiogram import flags

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    get_biggest_lastfm_image,
    get_lastfm_user_or_reply,
    handle_lastfm_error,
    reply_with_optional_image,
)
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Shows your Last.fm profile statistics."))
@flags.disableable(name="lfmuser")
class LastFMUserHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("lfmuser"),)

    async def handle(self) -> None:
        last_fm_user = await get_lastfm_user_or_reply(self.event)
        if not last_fm_user:
            return

        last_fm = LastFMClient()
        try:
            user_info = await last_fm.get_user_info(last_fm_user)
        except LastFMError as exc:
            await handle_lastfm_error(self.event, exc)
            return

        registered = datetime.fromtimestamp(user_info.registered, tz=UTC).strftime("%d-%m-%Y")
        user_mention = self.event.from_user.mention_html() if self.event.from_user else last_fm_user
        image = await get_biggest_lastfm_image(user_info)

        text = _(
            "User: <b>{user}</b>\n\n"
            "Total scrobbles: <code>{playcount}</code>\n"
            "Tracks scrobbled: <code>{track_count}</code>\n"
            "Artists scrobbled: <code>{artist_count}</code>\n"
            "Albums scrobbled: <code>{album_count}</code>\n"
            "\nRegistered: <i>{registered}</i>"
        ).format(
            user=user_mention,
            playcount=user_info.playcount,
            track_count=user_info.track_count,
            artist_count=user_info.artist_count,
            album_count=user_info.album_count,
            registered=registered,
        )

        await reply_with_optional_image(self.event, text, image)
