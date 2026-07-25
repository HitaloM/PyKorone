from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.args import WordArg, define_arguments
from korone.db.repositories.disabling import DisablingRepository
from korone.filters.admin_rights import UserRestricting
from korone.modules.disabling.utils.get_disabled import get_cmd_help_by_name, get_disabled_handlers
from korone.modules.help.utils.format_help import format_cmd
from korone.utils.formatting import Code, Italic, KeyValue, Section, Template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Re-enable a command in this chat."))
class EnableHandler(KoroneMessageHandler):
    arguments = define_arguments(cmd=WordArg(l_("Command")))

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("enable"), UserRestricting(admin=True))

    @staticmethod
    async def enable_cmd(chat_id: int, cmd: str) -> None:
        await DisablingRepository.enable(chat_id, cmd)

    async def handle(self) -> None:
        cmd_name: str = self.data["cmd"].lower().removeprefix("/")

        handler = get_cmd_help_by_name(cmd_name)

        if not handler:
            await self.event.reply(str(Template(_("Command {cmd} not found."), cmd=Code("/" + cmd_name))))
            return

        if handler not in await get_disabled_handlers(self.chat.chat_id):
            await self.event.reply(str(Template(_("Command {cmd} is already disabled."), cmd=Code("/" + cmd_name))))
            return

        await self.enable_cmd(self.chat.chat_id, handler.cmds[0])

        await self.event.reply(
            str(
                Section(
                    KeyValue(_("Chat"), self.chat.title),
                    KeyValue(_("Command"), format_cmd(handler.cmds[0])),
                    Italic(handler.description) if handler.description else None,
                    title=_("Command enabled"),
                )
            )
        )
