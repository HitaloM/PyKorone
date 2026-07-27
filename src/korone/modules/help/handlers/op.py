from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.constants import TELEGRAM_MESSAGE_LENGTH_LIMIT
from korone.filters.user_status import IsOP
from korone.modules.help.utils.extract_info import HELP_MODULES, HandlerHelp, ModuleHelp
from korone.modules.help.utils.format_help import format_handlers
from korone.utils.formatting import Section
from korone.utils.handlers import KoroneMessageHandler

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

OP_COMMANDS_MESSAGE_LENGTH_LIMIT = TELEGRAM_MESSAGE_LENGTH_LIMIT - 100


def _format_module_commands(module: ModuleHelp, handlers: list[HandlerHelp]) -> str:
    return str(Section(format_handlers(handlers), title=f"{module.name} {module.icon}"))


def _format_module_command_chunks(module: ModuleHelp) -> list[str]:
    handlers = [handler for handler in module.handlers if handler.only_op]
    if not handlers:
        return []

    module_text = _format_module_commands(module, handlers)
    if len(module_text) <= OP_COMMANDS_MESSAGE_LENGTH_LIMIT:
        return [module_text]

    return [_format_module_commands(module, [handler]) for handler in handlers]


def format_op_commands_messages(modules: list[ModuleHelp]) -> list[str]:
    messages: list[str] = []
    current_parts: list[str] = []
    current_length = 0

    for module in modules:
        for module_text in _format_module_command_chunks(module):
            separator_length = 2 if current_parts else 0
            next_length = current_length + separator_length + len(module_text)

            if current_parts and next_length > OP_COMMANDS_MESSAGE_LENGTH_LIMIT:
                messages.append("\n\n".join(current_parts))
                current_parts = [module_text]
                current_length = len(module_text)
                continue

            current_parts.append(module_text)
            current_length = next_length

    if current_parts:
        messages.append("\n\n".join(current_parts))

    return messages


@flags.help(description="List operator-only commands.")
class OpCMDSList(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return Command("op_cmds"), IsOP(is_op=True)

    async def handle(self) -> None:
        for text in format_op_commands_messages(list(HELP_MODULES.values())):
            await self.event.reply(text)
