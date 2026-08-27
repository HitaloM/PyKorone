from typing import TYPE_CHECKING, cast

from aiogram.enums import ButtonStyle
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InputRichBlockBlockQuotation,
    InputRichBlockParagraph,
    InputRichBlockSectionHeading,
    InputRichMessage,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F

from korone.filters.chat_status import PrivateChatFilter
from korone.modules.help.callbacks import HELP_START_PAYLOAD, PMHelpModule, PMHelpModules
from korone.modules.help.utils.extract_info import HELP_MODULES, get_aliased_cmds
from korone.modules.help.utils.format_help import (
    format_rich_examples,
    format_rich_handlers,
    format_rich_template,
    format_rich_text,
    group_handlers,
)
from korone.modules.help.utils.menu import build_rich_help_menu
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageCallbackQueryHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_
from korone.utils.telegram_errors import is_callback_query_expired_error

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InputRichBlockUnion

    from korone.modules.help.utils.extract_info import ModuleHelp


def _build_module_help(module_name: str, module: ModuleHelp) -> InputRichMessage:
    cmds = [handler for handler in module.handlers if not handler.only_op]

    rich_blocks: list[InputRichBlockUnion] = [InputRichBlockSectionHeading(text=f"{module.icon} {module.name}", size=1)]

    if module.description:
        rich_blocks.append(
            InputRichBlockBlockQuotation(blocks=[InputRichBlockParagraph(text=format_rich_text(module.description))])
        )
    if module.info:
        rich_blocks.append(InputRichBlockParagraph(text=format_rich_text(module.info)))

    for section_title, handlers in group_handlers(cmds):
        rich_blocks.extend((
            InputRichBlockSectionHeading(text=str(section_title), size=2),
            format_rich_handlers(handlers),
        ))

    for aliased_module_name, aliased_commands in get_aliased_cmds(module_name).items():
        aliased_module = HELP_MODULES[aliased_module_name]
        rich_blocks.extend((
            InputRichBlockSectionHeading(
                text=format_rich_template(
                    _("Shared commands from {module}"), module=f"{aliased_module.icon} {aliased_module.name}"
                ),
                size=2,
            ),
            format_rich_handlers(aliased_commands),
        ))

    if examples := format_rich_examples(cmds):
        rich_blocks.append(InputRichBlockSectionHeading(text=str(_("Examples")), size=2))
        rich_blocks.extend(examples)

    return InputRichMessage(blocks=rich_blocks)


class PMModulesList(KoroneMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router) -> None:
        router.message.register(
            cls,
            CommandStart(deep_link=True, magic=F.args == HELP_START_PAYLOAD),
            PrivateChatFilter(),
            flags={"help": {"exclude": True}},
        )
        router.message.register(
            cls, Command("help"), PrivateChatFilter(), flags={"help": {"description": l_("Show the full help menu.")}}
        )
        router.callback_query.register(cls, PMHelpModules.filter())

    async def handle(self) -> None:
        callback_data: PMHelpModules | None = self.data.get("callback_data", None)
        if isinstance(self.event, CallbackQuery):
            try:
                await self.event.answer()
            except TelegramBadRequest as error:
                if not is_callback_query_expired_error(error):
                    raise

        rich_message, reply_markup = build_rich_help_menu(callback_data)
        await self.answer_rich(rich_message, reply_markup=reply_markup)


class PMModuleHelp(KoroneCallbackQueryHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (PMHelpModule.filter(),)

    async def handle(self) -> None:
        callback_data = cast("PMHelpModule", self.callback_data)
        module_name = callback_data.module_name
        module = HELP_MODULES.get(module_name)

        if not module:
            await self.event.answer(_("Module not found."))
            return

        rich_message = _build_module_help(module_name, module)

        buttons = InlineKeyboardBuilder()

        buttons.button(
            text=_("⬅️ Back"),
            style=ButtonStyle.PRIMARY,
            callback_data=PMHelpModules(back_to_start=callback_data.back_to_start),
        )

        await self.check_for_message()
        await self.edit_rich(rich_message, reply_markup=buttons.as_markup())
        await self.event.answer()
