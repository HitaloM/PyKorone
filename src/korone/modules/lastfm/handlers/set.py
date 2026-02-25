from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from aiogram import flags
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ForceReply
from ass_tg.types import OptionalArg, WordArg
from stfu_tg import Code, Template

from korone.db.repositories.lastfm import LastFMRepository
from korone.filters.cmd import CMDFilter
from korone.modules.lastfm.utils import LastFMClient, LastFMError, format_lastfm_error
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


class LastFMSetState(StatesGroup):
    waiting_username = State()


def _normalize_username(raw_username: str) -> str:
    username = raw_username.strip()
    if username.startswith("@"):
        return username[1:]
    return username


async def _set_lastfm_username(message: Message, raw_username: str) -> bool:
    username = _normalize_username(raw_username)
    if not username or not USERNAME_RE.match(username):
        await message.reply(_("Invalid Last.fm username format."))
        return False

    if not message.from_user:
        await message.reply(_("Could not identify your Telegram user."))
        return False

    client = LastFMClient()
    try:
        exists = await client.user_exists(username=username)
    except LastFMError as exc:
        await message.reply(format_lastfm_error(exc))
        return False

    if not exists:
        await message.reply(_("Last.fm user not found."))
        return False

    await LastFMRepository.set_username(chat_id=message.from_user.id, username=username)
    await message.reply(
        Template(
            _("Last.fm username set to {username}. Use {command} to check your status."),
            username=Code(username),
            command=Code("/lfm"),
        ).to_html()
    )
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
        username = str(self.data.get("username") or "").strip()
        if username:
            await _set_lastfm_username(self.event, username)
            return

        await self.event.reply(_("Reply with your Last.fm username."), reply_markup=ForceReply(selective=True))
        await self.state.set_state(LastFMSetState.waiting_username)


@flags.help(exclude=True)
class LastFMSetReplyHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (StateFilter(LastFMSetState.waiting_username),)

    async def handle(self) -> None:
        if self.event.text and self.event.text.startswith(("/", "!")):
            raise SkipHandler

        await self.state.clear()

        if not self.event.text:
            await self.event.reply(_("Invalid Last.fm username format."))
            return

        await _set_lastfm_username(self.event, self.event.text)
