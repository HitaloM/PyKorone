from typing import Any, Optional

from aiogram import flags
from aiogram.handlers import BaseHandler, CallbackQueryHandler
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc, HList, Section, Title, Url

from sophie_bot import CONFIG
from sophie_bot.modules.help import PMHelpModule, PMHelpModules
from sophie_bot.modules.help.utils.extract_info import HELP_MODULES, get_aliased_cmds
from sophie_bot.modules.help.utils.format_help import format_cmds
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Shows help overview for all modules"))
class PMModulesList(BaseHandler[Message | CallbackQuery]):
    async def handle(self) -> Any:
        callback_data: Optional[PMHelpModules] = self.data.get("callback_data", None)

        buttons = InlineKeyboardBuilder().row(
            *(
                InlineKeyboardButton(
                    text=f"{module.icon} {module.name}",
                    callback_data=PMHelpModule(
                        module_name=module_name, back_to_start=bool(callback_data and callback_data.back_to_start)
                    ).pack(),
                )
                for module_name, module in HELP_MODULES.items()
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
        )

        if isinstance(self.event, CallbackQuery):
            await self.event.message.edit_text(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)  # type: ignore
        else:
            await self.event.reply(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)


class PMModuleHelp(CallbackQueryHandler):
    async def handle(self) -> Any:
        callback_data: PMHelpModule = self.data["callback_data"]
        module_name = callback_data.module_name
        module = HELP_MODULES.get(module_name)

        if not module:
            await self.event.answer(_("Module not found"))
            return

        cmds = list(filter(lambda x: not x.only_op, module.cmds))

        doc = Doc(
            HList(
                Title(f"{module.icon} {module.name}"),
                ("- " + module.description) if module.description else None,
            )
        )
        if module.info:
            doc += module.info

        doc += " "

        cmds_sec = Section(title=_("Commands"))
        pm_cmds_sec = Section(title=_("PM-only"))
        admin_only_cmds_sec = Section(title=_("Only admins"))

        for cmd in cmds:
            if cmd.only_pm:
                pm_cmds_sec += format_cmds([cmd])
            elif cmd.only_admin:
                admin_only_cmds_sec += format_cmds([cmd])
            else:
                cmds_sec += format_cmds([cmd])

        if cmds_sec:
            doc += cmds_sec

        if pm_cmds_sec:
            doc += pm_cmds_sec

        if admin_only_cmds_sec:
            doc += admin_only_cmds_sec

        for mod_name, cmds in get_aliased_cmds(module_name).items():
            module = HELP_MODULES[mod_name]
            doc += Section(
                format_cmds(cmds),
                title=_("Aliased commands from {module}").format(module=f"{module.icon} {module.name}"),
            )

        buttons = (
            InlineKeyboardBuilder()
            # .row(InlineKeyboardButton(text=_("📖 Wiki page"), url=CONFIG.wiki_link))
            .row(
                InlineKeyboardButton(
                    text=_("⬅️ Back"), callback_data=PMHelpModules(back_to_start=callback_data.back_to_start).pack()
                )
            )
        )

        if not self.event.message:
            raise SophieException("Message not found")

        await self.event.message.edit_text(str(doc), reply_markup=buttons.as_markup())  # type: ignore
