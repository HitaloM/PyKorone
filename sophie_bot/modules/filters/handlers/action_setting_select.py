from typing import Any

from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.callbacks import FilterSettingCallback
from sophie_bot.modules.filters.fsm import FilterEditFSM
from sophie_bot.modules.filters.handlers.action_select import ActionSelectHandler
from sophie_bot.modules.filters.types.modern_action_abc import ModernActionSetting
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _


class ActionSettingSelectHandler(ActionSelectHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            FilterSettingCallback.filter(),
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    async def handle(self) -> Any:
        data: FilterSettingCallback = self.data["callback_data"]
        filter_action = ALL_MODERN_ACTIONS[data.name]
        try:
            filters_item = await FilterInSetupType.get_filter(self.state, data=self.data)
        except ValueError:
            return await self.event.answer(_("Continuing setup is only possible by the same user who started it."))
        filter_action_data: Any = filters_item.actions[data.name]

        settings_item: ModernActionSetting = filter_action.settings(filter_action_data)[data.setting_name]

        if not settings_item.setup_message:
            raise SophieException("no setup message")

        await self.state.set_state(FilterEditFSM.action_change_settings)
        await self.state.update_data(
            action_name=data.name,
            action_setting=data.setting_name,
        )

        setup_message = await settings_item.setup_message(self.event, self.data)
        return await self._setup_message(
            settings_item.title,
            text=setup_message.text,
            reply_markup=setup_message.reply_markup,
            back_to_confirm=True,
        )
