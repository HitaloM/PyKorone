from typing import Any, Optional

from aiogram import Router, flags
from aiogram.handlers import CallbackQueryHandler
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc, HList, Section, Title, Url

from sophie_bot.config import CONFIG
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.callbacks import AIChatCallback
from sophie_bot.modules.help.callbacks import (
    PMHelpModule,
    PMHelpModules,
    PMHelpStartUrlCallback,
)
from sophie_bot.modules.help.utils.extract_info import HELP_MODULES, get_aliased_cmds
from sophie_bot.modules.help.utils.format_help import format_handlers, group_handlers
from sophie_bot.modules.utils_.base_handler import SophieMessageCallbackQueryHandler
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Shows help overview for all modules"))
class PMModulesList(SophieMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router):
        router.message.register(cls, PMHelpStartUrlCallback.filter(), ChatTypeFilter("private"))
        router.message.register(cls, CMDFilter("help"), ChatTypeFilter("private"))
        router.callback_query.register(cls, PMHelpModules.filter())

    async def handle(self) -> Any:
        callback_data: Optional[PMHelpModules] = self.data.get("callback_data", None)

        # Sort item by the module title
        modules = {k: v for k, v in sorted(HELP_MODULES.items(), key=lambda item: str(item[1].name)) if k != "ai"}
        # Put the featured module to the bottom
        if CONFIG.help_featured_module in HELP_MODULES:
            modules[CONFIG.help_featured_module] = HELP_MODULES[CONFIG.help_featured_module]

        buttons = InlineKeyboardBuilder()

        buttons.row(
            InlineKeyboardButton(text=_("💬✨ Chat with Sophie for help"), callback_data=AIChatCallback().pack())
        )

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
            buttons.row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data="go_to_start"))

        doc = Doc(
            Title(_("Help")),
            _("There are 2 help sources, you can read the detailed wiki or get a quick commands by modules overview."),
            Url(_("📖 Wiki (detailed information)"), CONFIG.wiki_link),
            " ",
            _("Alternatively you can now just chat with Sophie how to use herself!"),
        )

        if isinstance(self.event, CallbackQuery):
            await self.message.edit_text(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)
        else:
            await self.event.reply(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)


class PMModuleHelp(CallbackQueryHandler):
    async def handle(self) -> Any:
        callback_data: PMHelpModule = self.data["callback_data"]
        module_name = callback_data.module_name
        module = HELP_MODULES[module_name]

        if not module:
            await self.event.answer(_("Module not found"))
            return

        cmds = list(filter(lambda x: not x.only_op, module.handlers))

        doc = Doc(
            HList(
                Title(f"{module.icon} {module.name}"),
                f"- {module.description}" if module.description else None,
            )
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
                title=_("Aliased commands from {module}").format(module=f"{a_module.icon} {a_module.name}"),
            )

        buttons = InlineKeyboardBuilder()

        if module.advertise_wiki_page:
            doc += " "
            doc += Url(_("📖 Look the module's wiki page for more information"), CONFIG.wiki_modules_link + module_name)
            buttons.row(InlineKeyboardButton(text=_("📖 Wiki page"), url=CONFIG.wiki_modules_link + module_name))

        buttons.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=PMHelpModules(back_to_start=callback_data.back_to_start).pack()
            )
        )

        if not self.event.message:
            raise SophieException("Message not found")

        await self.event.message.edit_text(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)
