from typing import Any

from aiogram import flags
from aiogram.handlers import BaseHandler, CallbackQueryHandler
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Section, Title

from sophie_bot import CONFIG
from sophie_bot.modules.info import PMHelpBack, PMHelpModule
from sophie_bot.modules.info.utils.extract_info import HELP_MODULES
from sophie_bot.modules.info.utils.format_help import format_cmds
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Shows this message"))
class PMModulesList(BaseHandler[Message | CallbackQuery]):
    async def handle(self) -> Any:
        buttons = (
            InlineKeyboardBuilder()
            .add(InlineKeyboardButton(text=_("📖 Wiki (detailed information)"), url=CONFIG.wiki_link))
            .row(
                *(
                    InlineKeyboardButton(
                        text=f"{module.icon} {module.name}", callback_data=PMHelpModule(module_name=module_name).pack()
                    )
                    for module_name, module in HELP_MODULES.items()
                    if not module.exclude_public
                ),
                width=2,
            )
        )

        text = _("There are 2 help sources, you can read the detailed wiki or get a quick commands overview.")

        if isinstance(self.event, CallbackQuery):
            await self.event.message.edit_text(text, reply_markup=buttons.as_markup())  # type: ignore
        else:
            await self.event.reply(text, reply_markup=buttons.as_markup())


class PMModuleHelp(CallbackQueryHandler):
    async def handle(self) -> Any:
        callback_data: PMHelpModule = self.data["callback_data"]
        module_name = callback_data.module_name
        module = HELP_MODULES.get(module_name)

        if not module:
            await self.event.answer(_("Module not found"))
            return

        cmds = list(filter(lambda x: not x.only_op, module.cmds))

        doc = Title(f"{module.icon} {module.name}")
        if module.info:
            doc += module.info
            doc += " "

        if user_cmds := list(filter(lambda x: not x.only_admin, cmds)):
            doc += Section(format_cmds(user_cmds), title=_("Commands"))

        if admin_only_cmds := list(filter(lambda x: x.only_admin, cmds)):
            doc += Section(format_cmds(admin_only_cmds), title=_("Only admins"))

        buttons = (
            InlineKeyboardBuilder()
            .row(InlineKeyboardButton(text=_("📖 Wiki page"), url=CONFIG.wiki_link))
            .row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data=PMHelpBack().pack()))
        )

        if not self.event.message:
            raise SophieException("Message not found")

        await self.event.message.edit_text(str(doc), reply_markup=buttons.as_markup())  # type: ignore
