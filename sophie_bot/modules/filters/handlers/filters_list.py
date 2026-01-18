from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Doc, KeyValue, Section, Template

from sophie_bot.db.models import FiltersModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.filters.utils_.filter_action_text import filter_action_text
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.disableable(name="filters")
@flags.help(description=l_("Lists all filters in the chat"))
class FiltersListHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("filters"),)

    async def handle(self) -> Any:
        all_filters = await FiltersModel.get_filters(self.connection.tid)

        if not all_filters:
            return await self.event.reply(_("There are no filters in this chat!"))

        doc = Doc(
            Section(
                *(
                    KeyValue(item.handler, filter_action_text(item.action, list(item.actions.keys())), suffix=" -> ")
                    for item in all_filters
                ),
                title=Template(_("Filters in {chat_name}"), chat_name=self.connection.title),
            )
        )
        doc += " "
        doc += _("Additionally rules from 'Antiflood' module can be enforced.")
        await self.event.reply(doc.to_html())
