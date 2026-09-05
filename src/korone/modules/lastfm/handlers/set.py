from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.args import ArgumentSchema
from korone.db.repositories.lastfm import LastFMRepository
from korone.modules.lastfm.args import LastFMUsernameArg
from korone.modules.lastfm.handlers.base import LastFMHandlerSupport
from korone.modules.lastfm.utils import LastFMClient, LastFMError, format_lastfm_error
from korone.modules.utils_.reply_or_edit import reply_message
from korone.ui import Code, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message


@dataclass(frozen=True, slots=True)
class LastFMSetArguments:
    username: str | None = None


async def _set_lastfm_username(message: Message, username: str) -> bool:
    if not message.from_user:
        await reply_message(message, _("Could not identify your Telegram user."))
        return False

    client = LastFMClient()
    try:
        exists = await client.user_exists(username=username)
    except LastFMError as exc:
        await reply_message(message, format_lastfm_error(exc))
        return False

    if not exists:
        await reply_message(message, _("Last.fm user not found."))
        return False

    await LastFMRepository.set_username(chat_id=message.from_user.id, username=username)
    await reply_message(
        message,
        template(
            _("Last.fm username set to {username}. Use {command} to check your status."),
            username=Code(username),
            command=Code("/lfm"),
        ),
    )
    return True


@flags.help(description=l_("Set your Last.fm username for status commands."))
@flags.disableable(name="setlfm")
class LastFMSetHandler(KoroneMessageHandler[LastFMSetArguments]):
    arguments = ArgumentSchema(LastFMSetArguments, username=LastFMUsernameArg(l_("Username")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("setlfm"),)

    async def handle(self) -> None:
        username = self.args.username
        if username:
            await _set_lastfm_username(self.event, username)
            return

        await LastFMHandlerSupport.reply_missing_username(self.event)
