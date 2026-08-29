from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.args import WordArg, define_arguments
from korone.db.repositories.disabling import DisablingRepository
from korone.filters.admin_rights import UserRestricting
from korone.modules.disabling.utils.get_disabled import get_cmd_help_by_name, get_disabled_handlers
from korone.modules.help.utils.format_help import format_cmd
from korone.ui import Code, Italic, field, section, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Disable a command in this chat."), examples=((l_("Disable a command"), "help"),))
class DisableHandler(KoroneMessageHandler):
    arguments = define_arguments(cmd=WordArg(l_("Command")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("disable"), UserRestricting(admin=True))

    @staticmethod
    async def disable_cmd(chat_id: int, cmd: str) -> None:
        await DisablingRepository.disable(chat_id, cmd)

    async def handle(self) -> None:
        cmd_name: str = self.data["cmd"].lower().removeprefix("/")

        handler = get_cmd_help_by_name(cmd_name)

        if not handler:
            await self.answer(template(_("Command {cmd} not found."), cmd=Code("/" + cmd_name)))
            return

        if handler in await get_disabled_handlers(self.chat.chat_id):
            await self.answer(template(_("Command {cmd} is already disabled."), cmd=Code("/" + cmd_name)))
            return

        await self.disable_cmd(self.chat.chat_id, handler.cmds[0])
        await self.answer(
            section(
                _("Command disabled"),
                field(_("Chat"), self.chat.title),
                field(_("Command"), format_cmd(handler.cmds[0])),
                Italic(handler.description) if handler.description else None,
            )
        )
