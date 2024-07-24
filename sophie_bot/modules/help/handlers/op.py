from aiogram.handlers import MessageHandler
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Doc, HList, KeyValue, Section, VList

from sophie_bot.modules.help.cmds import CmdHelp


class OpCMDSList(MessageHandler):
    def format_cmd(self, cmd: str):
        return f"/{cmd}"

    def format_cmd_args(self, args: dict[str, ArgFabric]):
        return HList(*(f"<{arg.description}>" for arg in args.values()))

    def format_cmds(self, all_cmds: list[CmdHelp]):
        return VList(*(
            KeyValue(
                HList(*(self.format_cmd(cmd) for cmd in cmds.cmds)),
                self.format_cmd_args(cmds.args) if cmds.args else "",
                title_bold=False,
            )
            for cmds in all_cmds
        ))

    def handle(self):
        from sophie_bot.modules.help import HELP_MODULES

        return self.event.reply(
            str(
                Doc(*(
                    Section(self.format_cmds(module.cmds), title=f"{module.name} {module.icon}")
                    for module in HELP_MODULES
                ))
            )
        )
