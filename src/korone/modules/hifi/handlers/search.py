from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import flags
from aiogram.utils.chat_action import ChatActionSender
from ass_tg.types import TextArg

from korone.filters.cmd import CMDFilter
from korone.modules.hifi.utils.client import HifiAPIError, search_tracks
from korone.modules.hifi.utils.formatters import build_search_results_text
from korone.modules.hifi.utils.keyboard import create_tracks_keyboard
from korone.modules.hifi.utils.session import create_search_session
from korone.modules.hifi.utils.types import HifiSearchSession
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


@flags.help(description=l_("Search music with HiFi API."))
@flags.disableable(name="hifi")
class HifiSearchHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"query": TextArg(l_("Query"))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("song", "music", "hifi")),)

    async def handle(self) -> None:
        query = str(self.data.get("query") or "").strip()

        if not self.event.from_user:
            msg = "User information is not available in the handler context."
            raise RuntimeError(msg)

        try:
            async with ChatActionSender.typing(chat_id=self.event.chat.id, bot=self.bot):
                tracks = await search_tracks(query)
        except HifiAPIError:
            await self.event.reply(_("Could not fetch tracks right now. Please try again later."))
            return

        if not tracks:
            await self.event.reply(_("No tracks found."))
            return

        search_session = HifiSearchSession(user_id=self.event.from_user.id, query=query, tracks=tracks)
        session_token = await create_search_session(
            search_session.user_id, search_session.query, search_session.tracks
        )

        text = build_search_results_text(query=search_session.query, total_count=len(search_session.tracks), page=1)
        keyboard = create_tracks_keyboard(
            session=search_session, token=session_token, page=1, user_id=self.event.from_user.id
        )
        await self.event.reply(text, reply_markup=keyboard)
