from typing import Any

from aiogram.handlers import BaseHandler, CallbackQueryHandler
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Section, Title

from sophie_bot import CONFIG
from sophie_bot.modules.help import HELP_MODULES, PMHelpModule
from sophie_bot.modules.help.callbacks import PMHelpBack
from sophie_bot.modules.help.format_help import format_cmds
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _


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
            await self.event.answer("Module not found")
            return

        cmds = list(filter(lambda x: not x.only_op, module.cmds))

        doc = Title(f"{module.icon} {module.name}")

        doc += Section(format_cmds(list(filter(lambda x: not x.only_admin, cmds))), title="Commands")

        doc += Section(format_cmds(list(filter(lambda x: x.only_admin, cmds))), title="Only admins")

        buttons = (
            InlineKeyboardBuilder()
            .row(InlineKeyboardButton(text=_("📖 Wiki page"), url=CONFIG.wiki_link))
            .row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data=PMHelpBack().pack()))
        )

        if not self.event.message:
            raise SophieException("Message not found")

        await self.event.message.edit_text(str(doc), reply_markup=buttons.as_markup())  # type: ignore
