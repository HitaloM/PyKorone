from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Bold, Title

from sophie_bot.db.models import RulesModel
from sophie_bot.db.models.chat import ChatType
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Gets chat rules"))
@flags.disableable(name="rules")
class GetRulesHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("rules"),)

    async def handle(self) -> Any:
        connection = self.connection

        if not connection.is_connected and connection.type == ChatType.private:
            return await self.event.reply(_("Private chats can not have rules. Have fun."))

        rules = await RulesModel.get_rules(connection.tid)

        if not rules:
            return await self.event.reply(_("No rules are set for this chat."))

        title = Bold(Title(f"🪧 {_('Rules')}"))

        await send_saveable(
            self.event,
            self.event.chat.id,
            rules,
            title=title,
            reply_to=self.event.message_id,
            connection=connection,
        )
