from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import WordArg
from stfu_tg import Code, Italic, KeyValue, Section, Template

from korone.db.models.disabling import DisablingModel
from korone.filters.admin_rights import UserRestricting
from korone.filters.cmd import CMDFilter
from korone.modules.disabling.utils.get_disabled import get_cmd_help_by_name, get_disabled_handlers
from korone.modules.help.utils.format_help import format_cmd
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_


@flags.args(cmd=WordArg(l_("Command")))
@flags.help(description=l_("Disables the command."))
class DisableHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("disable"), UserRestricting(admin=True)

    @staticmethod
    async def disable_cmd(chat_id: int, cmd: str) -> None:
        await DisablingModel.disable(chat_id, cmd)

    async def handle(self):
        cmd_name: str = self.data["cmd"].lower().removeprefix("/").removeprefix("!")

        handler = get_cmd_help_by_name(cmd_name)

        if not handler:
            await self.event.reply(str(Template(_("Command {cmd} not found."), cmd=Code("/" + cmd_name))))
            return

        if handler in await get_disabled_handlers(self.chat.tid):
            await self.event.reply(str(Template(_("Command {cmd} is already disabled."), cmd=Code("/" + cmd_name))))
            return

        await self.disable_cmd(self.chat.tid, handler.cmds[0])
        await self.event.reply(
            str(
                Section(
                    KeyValue(_("Chat"), self.chat.title),
                    KeyValue(_("Command"), format_cmd(handler.cmds[0])),
                    Italic(handler.description) if handler.description else None,
                    title=_("Command disabled"),
                )
            )
        )
