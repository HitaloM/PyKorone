from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc

from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.callbacks import (
    FilterConfirm,
    ListActionsToRemoveCallback,
    RemoveFilterActionCallback,
)
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.filters.utils_.filter_action_text import get_modern_action_text
from sophie_bot.utils.handlers import SophieCallbackQueryHandler
from sophie_bot.utils.i18n import gettext as _


class ActionsListToRemoveHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            ListActionsToRemoveCallback.filter(),
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    async def handle(self) -> Any:
        try:
            filter_item = await FilterInSetupType.get_filter(self.state, data=self.data)
        except ValueError:
            return await self.event.answer(_("Continuing setup is only possible by the same user who started it."))

        # Construct the message
        doc = Doc(
            self.data.get("additional_doc", None),
            _("Select a filter action to remove:"),
        )

        buttons = InlineKeyboardBuilder()
        for filter_action in filter_item.actions.keys():
            action_title = get_modern_action_text(ALL_MODERN_ACTIONS[filter_action])

            buttons.row(
                InlineKeyboardButton(
                    text=action_title,
                    callback_data=RemoveFilterActionCallback(name=filter_action).pack(),
                )
            )

        buttons.row(
            InlineKeyboardButton(text=_("⬅️ Do not remove actions (Back)"), callback_data=FilterConfirm().pack())
        )

        await self.edit_text(doc.to_html(), reply_markup=buttons.as_markup())
