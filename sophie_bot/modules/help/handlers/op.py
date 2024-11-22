from aiogram.handlers import MessageHandler
from stfu_tg import Doc, Section

from sophie_bot.modules.help.utils.extract_info import HELP_MODULES
from sophie_bot.modules.help.utils.format_help import format_handlers


class OpCMDSList(MessageHandler):
    def handle(self):
        return self.event.reply(
            str(
                Doc(
                    *(
                        Section(format_handlers(module.handlers), title=f"{module.name} {module.icon}")
                        for module in HELP_MODULES.values()
                    )
                )
            )
        )
