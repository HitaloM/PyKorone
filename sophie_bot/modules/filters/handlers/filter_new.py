from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import TextArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Doc, Section, Title

from sophie_bot.db.models.filters import FilterHandlerType, FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.handlers.actions_list import ActionsListHandler
from sophie_bot.modules.filters.utils_.legacy_filter_handler import (
    check_legacy_filter_handler,
    text_legacy_handler_handles_on,
)
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Adds a new filter"))
class FilterNewHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter(
                ("addfilter", "newfilter"),
            ),
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {"handler": TextArg(l_("Text to match"))}

    async def handle(self) -> Any:
        keyword: str = self.data["handler"]
        await check_legacy_filter_handler(self.event, keyword, self.connection)

        # Create a new filter item
        filter_item = FilterInSetupType(handler=FilterHandlerType(keyword=keyword), actions={})
        await filter_item.set_filter_state(self.state)

        # Set handler text to state data
        self.data["additional_doc"] = Doc(
            Title(_("New filter")),
            Section(text_legacy_handler_handles_on(keyword), title=_("Handles")),
            " ",
        )
        self.data["cancel_button"] = True
        return await ActionsListHandler(self.event, **self.data)
