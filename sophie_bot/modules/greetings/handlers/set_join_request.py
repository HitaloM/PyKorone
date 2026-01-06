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
@flags.help(description=l_("Sets join request message."))
class SetJoinRequestMessageHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("setjoinrequest"), UserRestricting(admin=True)

    async def handle(self) -> Any:
        connection = self.connection
        raw_text = self.data.get("raw_text")

        saveable = await parse_saveable(self.event, raw_text)
        await GreetingsModel.change_join_request_message(connection.tid, saveable)

        doc = Doc(
            Template(_("Join request message was saved in {chat_title}."), chat_title=Italic(connection.title)),
        )

        await self.event.reply(str(doc))


@flags.help(description=l_("Deletes the join request message"))
class DelJoinRequestMessageHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("deljoinrequest"), UserRestricting(admin=True)

    async def handle(self) -> Any:
        connection = self.connection

        db_model = await GreetingsModel.get_by_chat_id(connection.tid)
        if not db_model or not db_model.join_request_message:
            return await self.event.reply(
                _("Join request message in {chat_title} has not been set before").format(chat_title=connection.title)
            )

        # Reset to None
        db_model.join_request_message = None
        await db_model.save()

        doc = Doc(
            Template(
                _("Join request message was reset to default in {chat_title}."), chat_title=Italic(connection.title)
            ),
        )

        await self.event.reply(str(doc))
