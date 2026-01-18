from typing import Any, Optional

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from stfu_tg import Doc, Title

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.callbacks import FilterActionCallback, FilterConfirm
from sophie_bot.modules.filters.fsm import FilterEditFSM
from sophie_bot.modules.filters.handlers.action_setup_confirm import (
    ActionSetupConfirmHandler,
)
from sophie_bot.modules.filters.types.modern_action_abc import ModernActionABC
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.troubleshooters.callbacks import CancelCallback
from sophie_bot.utils.handlers import SophieCallbackQueryHandler
from sophie_bot.modules.utils_.reply_or_edit import reply_or_edit
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import gettext as _


class ActionSelectHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            FilterActionCallback.filter(),
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    async def _setup_message(
        self,
        filter_title: LazyProxy,
        text: LazyProxy | str,
        reply_markup: Optional[InlineKeyboardMarkup],
        back_to_confirm: bool = False,
    ):
        doc = Doc(Title(f"{filter_title} {_('setup')}"), text)

        if not reply_markup:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[])

        reply_markup.inline_keyboard.append(
            [
                (
                    InlineKeyboardButton(text=_("⬅ Back"), callback_data=FilterConfirm().pack())
                    if back_to_confirm
                    else InlineKeyboardButton(
                        text=_("❌ Cancel"), callback_data=CancelCallback(user_id=self.event.from_user.id).pack()
                    )
                ),
            ]
        )

        # TODO: Need this??
        return await reply_or_edit(self.event, doc.to_html(), reply_markup=reply_markup)

    async def _filter_setup(self, filter_action: ModernActionABC):
        await self.state.update_data(
            filter_action_setup=filter_action.name,
        )

        await self.state.set_state(FilterEditFSM.action_setup)

        setup_message = await filter_action.interactive_setup.setup_message(self.event, self.data)  # type: ignore[union-attr, misc]
        return await self._setup_message(
            filter_action.title, text=setup_message.text, reply_markup=setup_message.reply_markup
        )

    async def handle(self) -> Any:
        data: FilterActionCallback = self.data["callback_data"]
        filter_action = ALL_MODERN_ACTIONS[data.name]

        if filter_action.interactive_setup and filter_action.interactive_setup.setup_message:
            return await self._filter_setup(filter_action)

        # Requires no additional setup procedure
        self.data["filter_action_setup"] = filter_action.name
        return await ActionSetupConfirmHandler(self.event, **self.data)
