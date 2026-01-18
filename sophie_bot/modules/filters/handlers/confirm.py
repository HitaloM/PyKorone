from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc, HList, Section, Title, VList
from typing_extensions import Optional

from sophie_bot.modules.filters.utils_.filter_abc import (
    ALL_FILTER_ACTIONS,
    FilterActionABC,
)
from sophie_bot.modules.filters.utils_.legacy_filter_handler import text_legacy_handler_handles_on
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import ngettext as pl_


class ConfirmAddFilter(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        # We don't need to register this handler as it'll be called from other handlers
        return (lambda *_: False,)

    async def handle(self) -> Any:
        filter_handler: Optional[str] = await self.state.get_value("filter_handler")
        filters_raw: Optional[dict[str, Any]] = await self.state.get_value("filters")

        if not filter_handler:
            raise ValueError("No filter handler in state")
        elif not filters_raw:
            raise ValueError("No filters in state")

        filters: tuple[tuple[FilterActionABC, Any], ...] = tuple(
            (ALL_FILTER_ACTIONS[filter_name], filter_data) for filter_name, filter_data in filters_raw.items()
        )

        doc = Doc(
            Title(_("New filter")),
            Section(text_legacy_handler_handles_on(filter_handler), title=_("Handles")),
            Section(
                VList(
                    *(
                        HList(filter_action.icon, filter_action.description(filter_data))
                        for filter_action, filter_data in filters
                    )
                ),
                title=pl_("Action", "Actions", len(filters)),
            ),
        )

        buttons = InlineKeyboardBuilder()

        for filter_action, _f in filters:
            for setting in filter_action.settings:
                buttons.row(InlineKeyboardButton(text=f"{setting.icon} {setting.title}", callback_data="todo"))

        buttons.row(
            InlineKeyboardButton(text=_("➕ Add another action"), callback_data="todo"),
        )

        buttons.row(
            InlineKeyboardButton(text=_("🚫 Cancel"), callback_data="todo"),
            InlineKeyboardButton(text=_("✅ Confirm"), callback_data="todo"),
        )

        await self.event.reply(str(doc), disable_web_page_preview=True, reply_markup=buttons.as_markup())
