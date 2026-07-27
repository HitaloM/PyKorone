from typing import TYPE_CHECKING, cast

from aiogram.enums import ButtonStyle
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InputRichMessage, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F

from korone.filters.chat_status import PrivateChatFilter
from korone.modules.help.callbacks import HELP_START_PAYLOAD, PMHelpModule, PMHelpModules
from korone.modules.help.utils.extract_info import HELP_MODULES, get_aliased_cmds
from korone.modules.help.utils.format_help import (
    format_examples,
    format_handler_item,
    format_handlers,
    format_rich_examples,
    group_handlers,
)
from korone.modules.help.utils.menu import build_help_menu, build_rich_help_menu
from korone.utils.formatting import (
    Doc,
    Heading,
    HList,
    ListItem,
    Paragraph,
    RichBlockQuote,
    Section,
    Template,
    Title,
    UnorderedList,
)
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageCallbackQueryHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.modules.help.utils.extract_info import ModuleHelp


def _build_module_help(module_name: str, module: ModuleHelp) -> tuple[str, InputRichMessage]:
    cmds = [handler for handler in module.handlers if not handler.only_op]

    legacy_doc = Doc(
        HList(Title(f"{module.icon} {module.name}"), f"- {module.description}" if module.description else None)
    )
    rich_doc = Doc(Heading(f"{module.icon} {module.name}"))

    if module.description:
        rich_doc += RichBlockQuote(module.description)
    if module.info:
        legacy_doc += module.info
        rich_doc += Paragraph(module.info)

    for section_title, handlers in group_handlers(cmds):
        legacy_doc += ""
        legacy_doc += Section(*format_handlers(handlers), title=section_title)
        rich_doc += Heading(section_title, level=2)
        rich_doc += UnorderedList(*(ListItem(format_handler_item(handler)) for handler in handlers))

    for aliased_module_name, aliased_commands in get_aliased_cmds(module_name).items():
        aliased_module = HELP_MODULES[aliased_module_name]
        title = Template(_("Shared commands from {module}"), module=f"{aliased_module.icon} {aliased_module.name}")
        legacy_doc += ""
        legacy_doc += Section(format_handlers(aliased_commands), title=title)
        rich_doc += Heading(title, level=2)
        rich_doc += UnorderedList(*(ListItem(format_handler_item(handler)) for handler in aliased_commands))

    if examples := format_examples(cmds):
        legacy_doc += ""
        legacy_doc += examples
        rich_doc += Heading(_("Examples"), level=2)
        rich_doc += Doc(*format_rich_examples(cmds))

    return str(legacy_doc), InputRichMessage(html=str(rich_doc))


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
        if self.message.ephemeral_message_id is not None:
            text, reply_markup = build_help_menu(callback_data)
            await self.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)
        else:
            rich_message, reply_markup = build_rich_help_menu(callback_data)
            await self.answer_rich(rich_message, reply_markup=reply_markup)

        if isinstance(self.event, CallbackQuery):
            await self.event.answer()


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

        text, rich_message = _build_module_help(module_name, module)

        buttons = InlineKeyboardBuilder()

        buttons.button(
            text=_("⬅️ Back"),
            style=ButtonStyle.PRIMARY,
            callback_data=PMHelpModules(back_to_start=callback_data.back_to_start),
        )

        await self.check_for_message()
        message = self.event.message
        if isinstance(message, Message) and message.ephemeral_message_id is not None:
            await self.edit_text(text, reply_markup=buttons.as_markup(), disable_web_page_preview=True)
        else:
            await self.edit_rich(rich_message, reply_markup=buttons.as_markup())
        await self.event.answer()
