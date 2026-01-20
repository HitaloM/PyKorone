from typing import Any

from aiogram import Router
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc, HList, Section, Title, VList

from sophie_bot.constants import FILTERS_MAX_TRIGGERS
from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.callbacks import (
    FilterConfirm,
    FilterSettingCallback,
    ListActionsToRemoveCallback,
    NewFilterActionCallback,
    SaveFilterCallback,
)
from sophie_bot.modules.filters.types.modern_action_abc import ModernActionABC
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.filters.utils_.legacy_filter_handler import text_legacy_handler_handles_on
from sophie_bot.modules.troubleshooters.callbacks import CancelCallback
from sophie_bot.utils.handlers import SophieMessageCallbackQueryHandler
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import ngettext as pl_


class FilterConfirmHandler(SophieMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router):
        router.callback_query.register(
            cls,
            FilterConfirm.filter(),
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    async def handle(self) -> Any:
        try:
            filter_item = await FilterInSetupType.get_filter(self.state, data=self.data)
        except ValueError:
            return await self.event.answer(_("Continuing setup is only possible by the same user who started it."))

        filters: tuple[tuple[ModernActionABC, Any], ...] = tuple(
            (ALL_MODERN_ACTIONS[filter_name], filter_data) for filter_name, filter_data in filter_item.actions.items()
        )

        doc = Doc(
            Title(_("New filter")),
            Section(text_legacy_handler_handles_on(filter_item.handler.keyword), title=_("Handles")),
            Section(
                VList(
                    *(
                        HList(
                            filter_action.icon,
                            filter_action.description(
                                filter_action.data_object(**filter_data) if filter_data else None
                            ),
                        )
                        for filter_action, filter_data in filters
                    )
                ),
                title=pl_("Action", "Actions", len(filters)),
            ),
        )

        buttons = InlineKeyboardBuilder()

        for filter_action, filter_data in filters:
            for setting_name, setting in filter_action.settings(filter_data).items():
                buttons.row(
                    InlineKeyboardButton(
                        text=f"{setting.icon} {setting.title}",
                        callback_data=FilterSettingCallback(name=filter_action.name, setting_name=setting_name).pack(),
                    )
                )

        # Manage filter actions buttons group
        manage_action_btn_row = []
        if len(filters) <= FILTERS_MAX_TRIGGERS:
            manage_action_btn_row.append(
                InlineKeyboardButton(
                    text=_("➕ Add another action"), callback_data=NewFilterActionCallback(back_to_confirm=True).pack()
                )
            )
        if len(filters) > 1:
            manage_action_btn_row.append(
                InlineKeyboardButton(text=_("➖ Remove actions"), callback_data=ListActionsToRemoveCallback().pack())
            )
        if manage_action_btn_row:
            buttons.row(*manage_action_btn_row)

        if not self.event.from_user:
            raise SophieException("No user in event")

        buttons.row(
            InlineKeyboardButton(
                text=_("🚫 Cancel"), callback_data=CancelCallback(user_id=self.event.from_user.id).pack()
            ),
            InlineKeyboardButton(text=_("✅ Confirm"), callback_data=SaveFilterCallback().pack()),
        )

        return await self.answer(doc.to_html(), disable_web_page_preview=True, reply_markup=buttons.as_markup())
