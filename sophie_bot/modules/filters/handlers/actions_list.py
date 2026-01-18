from typing import Any, Optional

from aiogram import Router
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc

from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.callbacks import (
    FilterActionCallback,
    FilterConfirm,
    NewFilterActionCallback,
)
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.utils.handlers import SophieMessageCallbackQueryHandler
from sophie_bot.utils.i18n import gettext as _


class ActionsListHandler(SophieMessageCallbackQueryHandler):
    """Lists all available filter actions. Can be executed as the "add new filter" action or right after trying to add a new filter."""

    @classmethod
    def register(cls, router: Router):
        router.callback_query.register(
            cls,
            NewFilterActionCallback.filter(),
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    async def handle(self) -> Any:
        callback_data: Optional[NewFilterActionCallback] = self.callback_data
        try:
            filter_item = await FilterInSetupType.get_filter(self.state, data=self.data)
        except ValueError:
            return await self.event.answer(_("Continuing setup is only possible by the same user who started it."))

        # Limit for actions that are not added already
        available_actions = list(
            action
            for action in ALL_MODERN_ACTIONS.values()
            if not any(action.name == added_action for added_action in filter_item.actions)
        )

        # Construct the message
        doc = (
            Doc(
                self.data.get("additional_doc", None),
                _("Select a filter action:"),
            )
            if available_actions
            else Doc(_("No additional actions available."))
        )

        buttons = InlineKeyboardBuilder()
        for filter_action in available_actions:
            buttons.row(
                InlineKeyboardButton(
                    text=f"{filter_action.icon} {filter_action.title}",
                    callback_data=FilterActionCallback(name=filter_action.name).pack(),
                )
            )

        buttons.adjust(2)

        if self.data.get("cancel_button"):
            buttons.row(InlineKeyboardButton(text=_("❌ Cancel"), callback_data="cancel"))
        elif callback_data and callback_data.back_to_confirm:
            buttons.row(
                InlineKeyboardButton(text=_("⬅️ Do not add an action (Back)"), callback_data=FilterConfirm().pack())
            )

        await self.answer(doc.to_html(), reply_markup=buttons.as_markup(), disable_web_page_preview=True)
