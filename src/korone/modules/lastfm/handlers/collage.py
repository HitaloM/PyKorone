from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, ClassVar

from aiogram import flags
from aiogram.types import BufferedInputFile
from aiogram.utils.chat_action import ChatActionSender
from ass_tg.types import OptionalArg, TextArg
from stfu_tg import PreformattedHTML, Template

from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    create_album_collage,
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

    from korone.modules.lastfm.utils.lastfm_api import TimePeriod


@flags.help(description=l_("Generates a Last.fm collage of your top albums."))
@flags.disableable(name="lfmcollage")
class LastFMCollageHandler(KoroneMessageHandler):
    _background_tasks: ClassVar[set] = set()

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"args": OptionalArg(TextArg(l_("Args")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("lfmcollage"),)

    async def _generate_and_send(
        self, last_fm_user: str, collage_size: int, period: TimePeriod, *, show_text: bool
    ) -> None:
        async with ChatActionSender.upload_photo(chat_id=self.event.chat.id, bot=self.bot):
            last_fm = LastFMClient()
            try:
                top_items = await last_fm.get_top_albums(last_fm_user, period, limit=collage_size**2)
                if not top_items:
                    await self.event.reply(_("No top albums found for your Last.fm account."))
                    return

                collage_bytes = await create_album_collage(
                    top_items, collage_size=(collage_size, collage_size), show_text=show_text
                )

                user_link = get_user_link(self.event, last_fm_user)
                caption = Template(
                    "{user}\n{size}x{size}, albums, {period}",
                    user=PreformattedHTML(user_link),
                    size=collage_size,
                    period=period_to_str(period),
                ).to_html()

                file = BufferedInputFile(collage_bytes.getvalue(), filename="lastfm-collage.png")
                await self.event.reply_photo(photo=file, caption=caption)
            except LastFMError as exc:
                await handle_lastfm_error(self.event, exc)

    async def handle(self) -> None:
        last_fm_user = await get_lastfm_user_or_reply(self.event)
        if not last_fm_user:
            return

        args = (self.data.get("args") or "").strip()
        collage_size, period, _entry_type, no_text = parse_collage_arg(args)
        show_text = not no_text

        task = asyncio.create_task(self._generate_and_send(last_fm_user, collage_size, period, show_text=show_text))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
