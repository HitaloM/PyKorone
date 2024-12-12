from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Code, Doc, HList, Section, Template, Title, VList

from sophie_bot.modules.filters.utils_.filter_abc import (
    ALL_FILTER_ACTIONS,
    FilterActionABC,
)
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import ngettext as pl_


class ConfirmAddFilter(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        # We don't need to register this handler as it'll be called from other handlers
        return (lambda *_: False,)

    async def handle(self) -> Any:
        filter_handler: str = await self.state.get_value("filter_handler")
        filters_raw: dict[str, Any] = await self.state.get_value("filters")
        filters: list[tuple[FilterActionABC, Any]] = tuple(
            (ALL_FILTER_ACTIONS[filter_name], filter_data) for filter_name, filter_data in filters_raw.items()
        )

        if not filters:
            raise ValueError("No filter actions in state")

        doc = Doc(
            Title(_("New filter")),
            Section(Template(_("When {handler} in message"), handler=Code(filter_handler)), title=_("Handles")),
            Section(
                VList(
                    *(HList(filter_action.icon, filter_action.description(filter_data))
                    for filter_action, filter_data in filters)
                ),
                title=pl_("Action", "Actions", len(filters))
            ),
        )

        buttons = InlineKeyboardBuilder()

        for filter_action, _f in filters:
            for setting in filter_action.settings:
                buttons.row(InlineKeyboardButton(
                    text=f'{setting.icon} {setting.title}',
                    callback_data='todo'
                ))

        buttons.row(
            InlineKeyboardButton(text=_("➕ Add another action"), callback_data="todo"),
        )

        buttons.row(
            InlineKeyboardButton(text=_("🚫 Cancel"), callback_data="todo"),
            InlineKeyboardButton(text=_("✅ Confirm"), callback_data="todo"),
        )

        await self.event.reply(str(doc), disable_web_page_preview=True, reply_markup=buttons.as_markup())
