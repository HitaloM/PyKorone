from re import search
from typing import Any

from aiogram import F
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.filters import CommandStart
from stfu_tg import Bold, Section, Title

from sophie_bot.db.models import RulesModel
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _


class LegacyRulesButton(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CommandStart(deep_link=True, magic=F.args.regexp(r"btn_rules_")),)

    async def handle(self) -> Any:
        regex = search(r"btn_rules_(.*)", self.event.text)
        if not regex:
            return

        chat_id = int(regex.group(1))

        rules = await RulesModel.get_rules(chat_id)

        if not rules:
            return await self.event.reply(
                str(Section(_("No rules are set for this chat."), title=_("Rules button failed")))
            )

        title = Bold(Title(f"🪧 {_('Rules')}"))

        await send_saveable(
            self.event,
            self.event.chat.id,
            rules,
            title=title,
            reply_to=self.event.message_id,
            connection=self.connection,
        )
