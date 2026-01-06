from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import OptionalArg, TextArg
from stfu_tg import Doc, Italic, Template

from sophie_bot.db.models import GreetingsModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.notes.utils.parse import parse_saveable
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(raw_text=OptionalArg(TextArg(l_("Content"), parse_entities=True)))
@flags.help(description=l_("Sets welcome message."))
class SetWelcomeMessageHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("setwelcome"), UserRestricting(admin=True)

    async def handle(self) -> Any:
        connection = self.connection
        raw_text = self.data.get("raw_text")

        # Workaround for the old syntax
        if raw_text == "off":
            return await self.event.reply(
                str(
                    Template(
                        _("Please the '{cmd}' to control the welcome status."), cmd=Italic("/enablewelcome <on / off>")
                    )
                )
            )

        saveable = await parse_saveable(self.event, raw_text)
        await GreetingsModel.change_welcome_message(connection.tid, saveable)

        doc = Doc(
            Template(
                _("Welcome message was successfully updated in {chat_title}."), chat_title=Italic(connection.title)
            ),
            Template(_("Use {cmd} to retrieve the welcome message."), cmd=Italic("/welcome")),
        )
        db_model = await GreetingsModel.get_by_chat_id(connection.tid)
        if db_model and db_model.welcome_disabled:
            doc += " "
            doc += Template(
                _(
                    "⚠️ Please note, that the welcome messages are currently disabled in the chat, use '{cmd}' to enable it."
                ),
                cmd=Italic("/enablewelcome on"),
            )

        await self.event.reply(str(doc))
