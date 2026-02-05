from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from aiogram import flags
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ForceReply
from ass_tg.types import OptionalArg, WordArg

from korone.db.repositories.lastfm import LastFMRepository
from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import LastFMClient, LastFMError, handle_lastfm_error
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]+$")


class LastFMSetState(StatesGroup):
    waiting_username = State()


async def set_lastfm_username(message: Message, username: str) -> bool:
    if not USERNAME_RE.match(username):
        await message.reply(_("Last.fm username must not contain spaces or special characters!"))
        return False

    if not message.from_user:
        await message.reply(_("Could not identify your user."))
        return False

    last_fm = LastFMClient()
    try:
        await last_fm.get_user_info(username)
    except LastFMError as exc:
        await handle_lastfm_error(message, exc)
        return False

    await LastFMRepository.set_username(chat_id=message.from_user.id, username=username)
    await message.reply(_("Last.fm username set successfully!"))
    return True


@flags.help(description=l_("Set your Last.fm username."))
@flags.disableable(name="setlfm")
class LastFMSetHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"username": OptionalArg(WordArg(l_("Username")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("setlfm"),)

    async def handle(self) -> None:
        username = (self.data.get("username") or "").strip()
        if username:
            await set_lastfm_username(self.event, username)
            return

        await self.event.reply(_("Reply with your Last.fm username."), reply_markup=ForceReply(selective=True))
        await self.state.set_state(LastFMSetState.waiting_username)


class LastFMSetReplyHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (StateFilter(LastFMSetState.waiting_username),)

    async def handle(self) -> None:
        if self.event.text and self.event.text.startswith(("/", "!")):
            raise SkipHandler

        await self.state.clear()
        await set_lastfm_username(self.event, self.event.text or "")
