from typing import Any

from aiogram import Router
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Code, Doc, HList, Section, Template, Title, VList

from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.callbacks import (
    FilterConfirm,
    SaveFilterCallback,
)
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.troubleshooters.callbacks import CancelCallback
from sophie_bot.modules.utils_.base_handler import SophieMessageCallbackQueryHandler
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _


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
        filter_item = await FilterInSetupType.get_filter(self.state, data=self.data)

        # Build a simple summary of current action (single-action policy)
        actions = tuple(filter_item.actions.items())
        details = []
        for name, data in actions:
            action = ALL_MODERN_ACTIONS.get(name)
            if not action:
                continue
            try:
                desc = action.description(action.data_object(**data) if data else None)
            except Exception:
                desc = action.title
            details.append(HList(action.icon, desc))

        doc = Doc(
            Title(_("New filter")),
            Section(
                Template(_("When {handler} in message"), handler=Code(filter_item.handler.keyword)), title=_("Handles")
            ),
            Section(
                VList(*details) if details else VList(_("No action configured yet")),
                title=_("Action"),
            ),
        )

        buttons = InlineKeyboardBuilder()

        # Provide entry to ACW home page
        buttons.row(InlineKeyboardButton(text=_("⚙ Configure action"), callback_data="filter_action:back"))

        if not self.event.from_user:
            raise SophieException("No user in event")

        buttons.row(
            InlineKeyboardButton(
                text=_("🚫 Cancel"), callback_data=CancelCallback(user_id=self.event.from_user.id).pack()
            ),
            InlineKeyboardButton(text=_("✅ Confirm"), callback_data=SaveFilterCallback().pack()),
        )

        return await self.answer(doc.to_html(), disable_web_page_preview=True, reply_markup=buttons.as_markup())
