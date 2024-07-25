from aiogram.handlers import MessageHandler

from sophie_bot.modules.help import HELP_MODULES
from sophie_bot.modules.help.format_help import format_cmds
from stfu_tg import Doc, Section


class OpCMDSList(MessageHandler):


    def handle(self):
        return self.event.reply(
            str(
                Doc(*(
                    Section(format_cmds(module.cmds), title=f"{module.name} {module.icon}")
                    for module in HELP_MODULES.values()
                ))
            )
        )
