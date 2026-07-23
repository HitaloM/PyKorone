from typing import TYPE_CHECKING, cast

from aiogram.enums import ButtonStyle
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from stfu_tg import Doc, HList, Section, Template, Title

from korone.filters.chat_status import PrivateChatFilter
from korone.modules.help.callbacks import HELP_START_PAYLOAD, PMHelpModule, PMHelpModules
from korone.modules.help.utils.extract_info import HELP_MODULES, get_aliased_cmds
from korone.modules.help.utils.format_help import format_examples, format_handlers, group_handlers
from korone.modules.help.utils.menu import build_help_menu
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageCallbackQueryHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType


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
        text, reply_markup = build_help_menu(callback_data)
        await self.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)


class PMModuleHelp(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (PMHelpModule.filter(),)

    async def handle(self) -> None:
        callback_data = cast("PMHelpModule", self.callback_data)
        module_name = callback_data.module_name
        module = HELP_MODULES[module_name]

        if not module:
            await self.event.answer(_("Module not found."))
            return

        cmds = [handler for handler in module.handlers if not handler.only_op]

        doc = Doc(
            HList(Title(f"{module.icon} {module.name}"), f"- {module.description}" if module.description else None)
        )
        if module.info:
            doc += module.info

        for section_title, handlers in group_handlers(cmds):
            doc += ""
            doc += Section(*format_handlers(handlers), title=section_title)

        for a_mod_name, a_cmds in get_aliased_cmds(module_name).items():
            a_module = HELP_MODULES[a_mod_name]
            doc += ""
            doc += Section(
                format_handlers(a_cmds),
                title=Template(_("Shared commands from {module}"), module=f"{a_module.icon} {a_module.name}"),
            )

        if examples := format_examples(cmds):
            doc += ""
            doc += examples

        buttons = InlineKeyboardBuilder()

        buttons.button(
            text=_("⬅️ Back"),
            style=ButtonStyle.PRIMARY,
            callback_data=PMHelpModules(back_to_start=callback_data.back_to_start),
        )

        await self.check_for_message()
        await self.edit_text(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)
