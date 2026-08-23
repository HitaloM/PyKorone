import re
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.args import OptionalArg, WordArg, define_arguments
from korone.db.repositories.lastfm import LastFMRepository
from korone.modules.lastfm.handlers.base import LastFMHandlerSupport
from korone.modules.lastfm.utils import LastFMClient, LastFMError, format_lastfm_error
from korone.utils.formatting import Code, Template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


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


@flags.help(description=l_("Set your Last.fm username for status commands."))
@flags.disableable(name="setlfm")
class LastFMSetHandler(KoroneMessageHandler):
    arguments = define_arguments(username=OptionalArg(WordArg(l_("Username"))))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("setlfm"),)

    async def handle(self) -> None:
        username = str(self.data.get("username") or "").strip()
        if username:
            await _set_lastfm_username(self.event, username)
            return

        await LastFMHandlerSupport.reply_missing_username(self.event)
