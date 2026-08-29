from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.constants import TELEGRAM_MESSAGE_LENGTH_LIMIT
from korone.filters.user_status import IsOP
from korone.modules.help.utils.extract_info import HELP_MODULES, HandlerHelp, ModuleHelp
from korone.modules.help.utils.format_help import format_handlers
from korone.ui import MessageContent, UIExpression, column, section
from korone.ui.rendering import plain_text
from korone.utils.handlers import KoroneMessageHandler

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

OP_COMMANDS_MESSAGE_LENGTH_LIMIT = TELEGRAM_MESSAGE_LENGTH_LIMIT - 100


def _format_module_commands(module: ModuleHelp, handlers: list[HandlerHelp]) -> UIExpression:
    return section(f"{module.name} {module.icon}", format_handlers(handlers))


def _format_module_command_chunks(module: ModuleHelp) -> list[UIExpression]:
    handlers = [handler for handler in module.handlers if handler.only_op]
    if not handlers:
        return []

    module_text = _format_module_commands(module, handlers)
    if len(plain_text(module_text)) <= OP_COMMANDS_MESSAGE_LENGTH_LIMIT:
        return [module_text]

    return [_format_module_commands(module, [handler]) for handler in handlers]


def format_op_commands_messages(modules: list[ModuleHelp]) -> list[MessageContent]:
    messages: list[MessageContent] = []
    current_parts: list[UIExpression] = []
    current_length = 0

    for module in modules:
        for module_text in _format_module_command_chunks(module):
            separator_length = 2 if current_parts else 0
            module_length = len(plain_text(module_text))
            next_length = current_length + separator_length + module_length

            if current_parts and next_length > OP_COMMANDS_MESSAGE_LENGTH_LIMIT:
                messages.append(column(*current_parts, gap=1))
                current_parts = [module_text]
                current_length = module_length
                continue

            current_parts.append(module_text)
            current_length = next_length

    if current_parts:
        messages.append(column(*current_parts, gap=1))

    return messages


@flags.help(description="List operator-only commands.")
class OpCMDSList(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return Command("op_cmds"), IsOP(is_op=True)

    async def handle(self) -> None:
        for text in format_op_commands_messages(list(HELP_MODULES.values())):
            await self.answer(text)
