from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.enums import ButtonStyle
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Code, Doc, HList, Italic, Section, Template, Title, VList

from korone.filters.chat_status import PrivateChatFilter
from korone.filters.cmd import CMDFilter
from korone.modules.help.callbacks import PMHelpModule, PMHelpModules, PMHelpStartUrlCallback
from korone.modules.help.utils.extract_info import HELP_MODULES, get_aliased_cmds
from korone.modules.help.utils.format_help import format_handlers, group_handlers
from korone.modules.utils_.callbacks import GoToStartCallback
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageCallbackQueryHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Shows help overview for all modules"))
class PMModulesList(KoroneMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router) -> None:
        router.message.register(cls, PMHelpStartUrlCallback.filter(), PrivateChatFilter())
        router.message.register(cls, CMDFilter("help"), PrivateChatFilter())
        router.callback_query.register(cls, PMHelpModules.filter())

    async def handle(self) -> None:
        callback_data: PMHelpModules | None = self.data.get("callback_data", None)

        modules = dict(sorted(HELP_MODULES.items(), key=lambda item: str(item[1].name)))

        buttons = InlineKeyboardBuilder()

        buttons.row(
            *(
                InlineKeyboardButton(
                    text=f"{module.icon} {module.name}",
                    callback_data=PMHelpModule(
                        module_name=module_name, back_to_start=bool(callback_data and callback_data.back_to_start)
                    ).pack(),
                )
                for module_name, module in modules.items()
                if not module.exclude_public
            ),
            width=2,
        )

        if callback_data and callback_data.back_to_start:
            buttons.row(
                InlineKeyboardButton(
                    text=_("⬅️ Back"), style=ButtonStyle.PRIMARY, callback_data=GoToStartCallback().pack()
                )
            )

        doc = Doc(
            Title(_("Help")),
            _("Select a module to see its commands and information!"),
            Section(
                VList(
                    Template(
                        _("Arguments: {required} is required and {optional} is optional."),
                        required=Code("<arg>"),
                        optional=Code("<?arg>"),
                    ),
                    HList(Italic(_("— Only in groups")), _("means it works only in group chats.")),
                    HList(Italic(_("PM-only")), _("lists commands that only work in private chat.")),
                    HList(Italic(_("Only admins")), _("lists commands that require admin rights.")),
                    HList(
                        Italic(Template("({label})", label=_("Disable-able"))),
                        Template(
                            _("means the command can be toggled with {disable} and {enable}."),
                            disable=Code("/disable"),
                            enable=Code("/enable"),
                        ),
                    ),
                ),
                title=_("How to read /help"),
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
            await self.event.answer(_("Module not found"))
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
                title=Template(_("Aliased commands from {module}"), module=f"{a_module.icon} {a_module.name}"),
            )

        buttons = InlineKeyboardBuilder()

        buttons.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"),
                style=ButtonStyle.PRIMARY,
                callback_data=PMHelpModules(back_to_start=callback_data.back_to_start).pack(),
            )
        )

        await self.check_for_message()
        await self.edit_text(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)
