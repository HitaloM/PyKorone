from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.args import ArgumentSchema
from korone.db.repositories.disabling import DisablingRepository
from korone.filters.admin_rights import UserRestricting
from korone.modules.disabling.args import CommandArg
from korone.modules.disabling.utils.get_disabled import get_disabled_handlers
from korone.modules.help.utils.format_help import format_cmd
from korone.ui import Code, Italic, field, section, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.modules.disabling.args import CommandReference


@dataclass(frozen=True, slots=True)
class EnableArguments:
    command: CommandReference


@flags.help(description=l_("Re-enable a command in this chat."))
class EnableHandler(KoroneMessageHandler[EnableArguments]):
    arguments = ArgumentSchema(EnableArguments, command=CommandArg(l_("Command")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("enable"), UserRestricting(admin=True))

    @staticmethod
    async def enable_cmd(chat_id: int, cmd: str) -> None:
        await DisablingRepository.enable(chat_id, cmd)

    async def handle(self) -> None:
        command = self.args.command
        handler = command.handler
        cmd_name = command.name

        if handler not in await get_disabled_handlers(self.chat.chat_id):
            await self.answer(template(_("Command {cmd} is already enabled."), cmd=Code("/" + cmd_name)))
            return

        await self.enable_cmd(self.chat.chat_id, command.disableable_name)

        await self.answer(
            section(
                _("Command enabled"),
                field(_("Chat"), self.chat.title),
                field(_("Command"), format_cmd(handler.cmds[0])),
                Italic(handler.description) if handler.description else None,
            )
        )
