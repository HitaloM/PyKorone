from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from aiogram import flags
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ForceReply
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ass_tg.types import OptionalArg, WordArg
from magic_filter import F
from stfu_tg import Code, Template

from korone.db.repositories.lastfm import LastFMRepository
from korone.filters.chat_status import PrivateChatFilter
from korone.modules.lastfm.utils import LastFMClient, LastFMError, format_lastfm_error
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.fsm.context import FSMContext
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
LASTFM_SET_START_PAYLOAD = "lastfm_set"


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
        str(
            Template(
                _("Last.fm username set to {username}. Use {command} to check your status."),
                username=Code(username),
                command=Code("/lfm"),
            )
        )
    )
    return True


async def _prompt_for_username(message: Message, state: FSMContext) -> None:
    await message.reply(_("Reply with your Last.fm username."), reply_markup=ForceReply(selective=True))
    await state.set_state(LastFMSetState.waiting_username)


@flags.help(description=l_("Set your Last.fm username for status commands."))
@flags.disableable(name="setlfm")
class LastFMSetHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"username": OptionalArg(WordArg(l_("Username")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("setlfm"),)

    async def handle(self) -> None:
        username = str(self.data.get("username") or "").strip()
        if username:
            await self.state.clear()
            await _set_lastfm_username(self.event, username)
            return

        if self.chat.type == ChatType.PRIVATE:
            await self.state.clear()
            await _prompt_for_username(self.event, self.state)
            return

        private_url = await create_start_link(self.bot, LASTFM_SET_START_PAYLOAD)
        buttons = InlineKeyboardBuilder()
        buttons.button(text=_("Open private chat"), url=private_url)

        await self.event.reply(_("Tap the button below to continue in private."), reply_markup=buttons.as_markup())


@flags.help(exclude=True)
@flags.disableable(name="setlfm")
class LastFMSetStartHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CommandStart(deep_link=True, magic=F.args == LASTFM_SET_START_PAYLOAD), PrivateChatFilter())

    async def handle(self) -> None:
        await self.state.clear()
        await _prompt_for_username(self.event, self.state)


@flags.help(exclude=True)
class LastFMSetReplyHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (StateFilter(LastFMSetState.waiting_username), PrivateChatFilter())

    async def handle(self) -> None:
        if self.event.text and self.event.text.startswith("/"):
            raise SkipHandler

        await self.state.clear()

        if not self.event.text:
            await self.event.reply(_("Invalid Last.fm username format."))
            return

        await _set_lastfm_username(self.event, self.event.text)
