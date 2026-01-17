from typing import Any, Optional

from aiogram import Router
from aiogram.fsm.storage.base import DEFAULT_DESTINY

from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.fsm import FilterEditFSM
from sophie_bot.modules.filters.handlers.filter_confirm import FilterConfirmHandler
from sophie_bot.modules.filters.types.modern_action_abc import (
    ActionSetupTryAgainException,
    ModernActionSetting,
)
from sophie_bot.modules.filters.types.modern_action_data_types import (
    ACTION_DATA,
    ACTION_DATA_DUMPED,
)
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.utils_.base_handler import SophieMessageCallbackQueryHandler
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _


class ActionChangeSettingConfirm(SophieMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router):
        router.message.register(
            cls,
            FilterEditFSM.action_change_settings,
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    async def handle(self) -> Any:
        action_name: Optional[str] = await self.state.get_value("action_name")
        action_setting: Optional[str] = await self.state.get_value("action_setting")

        if not action_name or not action_setting:
            raise SophieException("No action name or setting in state/data")

        action_item = ALL_MODERN_ACTIONS[action_name]
        action_setting: ModernActionSetting = action_item.settings(self.data)[action_setting]

        # TODO: Deal with typing below
        try:
            action_data_model: ACTION_DATA | None = await action_setting.setup_confirm(self.event, self.data)  # type: ignore
        except ActionSetupTryAgainException:
            return

        action_data: ACTION_DATA_DUMPED = action_data_model.model_dump(mode="json") if action_data_model else None

        # Add action to the list
        try:
            filter_item = await FilterInSetupType.get_filter(self.state, data=self.data)
        except ValueError:
            return await self.event.answer(_("Continuing setup is only possible by the same user who started it."))
        filter_item.actions[action_name] = action_data
        await filter_item.set_filter_state(self.state)

        await self.state.set_state(DEFAULT_DESTINY)  # Reset to default state but do not flush the state data

        return await FilterConfirmHandler(self.event, **self.data)
