from typing import TYPE_CHECKING, cast

from aiogram.enums import ButtonStyle
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from stfu_tg import Code, Doc, HList, Italic, Section, Template, Title, VList

from korone.filters.chat_status import PrivateChatFilter
from korone.modules.help.callbacks import HELP_START_PAYLOAD, PMHelpModule, PMHelpModules
from korone.modules.help.utils.extract_info import HELP_MODULES, get_aliased_cmds
from korone.modules.help.utils.format_help import format_handlers, group_handlers
from korone.modules.utils_.callbacks import GoToStartCallback
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
            cls,
            Command("help"),
            PrivateChatFilter(),
            flags={"help": {"description": l_("Show the help menu with all modules.")}},
        )
        router.callback_query.register(cls, PMHelpModules.filter())

    async def handle(self) -> None:
        callback_data: PMHelpModules | None = self.data.get("callback_data", None)

        modules = dict(sorted(HELP_MODULES.items(), key=lambda item: str(item[1].name)))

        buttons = InlineKeyboardBuilder()
        module_buttons_count = 0

        for module_name, module in modules.items():
            if module.exclude_public:
                continue
            buttons.button(
                text=f"{module.icon} {module.name}",
                callback_data=PMHelpModule(
                    module_name=module_name, back_to_start=bool(callback_data and callback_data.back_to_start)
                ),
            )
            module_buttons_count += 1

        has_back_button = bool(callback_data and callback_data.back_to_start)
        if callback_data and callback_data.back_to_start:
            buttons.button(text=_("⬅️ Back"), style=ButtonStyle.PRIMARY, callback_data=GoToStartCallback())

        widths = [2] * (module_buttons_count // 2)
        if module_buttons_count % 2:
            widths.append(1)
        if has_back_button:
            widths.append(1)
        if widths:
            buttons.adjust(*widths)

        doc = Doc(
            Title(_("Help")),
            _("Select a module to view commands and usage details."),
            Section(
                VList(
                    Template(
                        _("Arguments: {required} is required, {optional} is optional."),
                        required=Code("<arg>"),
                        optional=Code("<?arg>"),
                    ),
                    HList(Italic(_("— Only in groups")), _("indicates commands available only in groups.")),
                    HList(Italic(_("PM-only")), _("lists commands available only in private chat.")),
                    HList(Italic(_("Only admins")), _("lists commands that require admin rights.")),
                    HList(
                        Italic(Template("({label})", label=_("Toggleable"))),
                        Template(
                            _("means admins can disable or re-enable the command with {disable} and {enable}."),
                            disable=Code("/disable"),
                            enable=Code("/enable"),
                        ),
                    ),
                ),
                title=_("/help legend"),
            ),
        )

        if isinstance(self.event, CallbackQuery):
            await self.message.edit_text(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)
        else:
            await self.event.reply(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)


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

        cmds = list(filter(lambda x: not x.only_op, module.handlers))

        doc = Doc(
            HList(Title(f"{module.icon} {module.name}"), f"- {module.description}" if module.description else None)
        )
        if module.info:
            doc += module.info

        doc += " "

        for section_title, handlers in group_handlers(cmds):
            doc += Section(*format_handlers(handlers), title=section_title)

        for a_mod_name, a_cmds in get_aliased_cmds(module_name).items():
            a_module = HELP_MODULES[a_mod_name]
            doc += Section(
                format_handlers(a_cmds),
                title=Template(_("Shared commands from {module}"), module=f"{a_module.icon} {a_module.name}"),
            )

        buttons = InlineKeyboardBuilder()

        buttons.button(
            text=_("⬅️ Back"),
            style=ButtonStyle.PRIMARY,
            callback_data=PMHelpModules(back_to_start=callback_data.back_to_start),
        )

        await self.check_for_message()
        await self.edit_text(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)
