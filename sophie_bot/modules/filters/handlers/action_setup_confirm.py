from typing import Any

from aiogram import Router
from aiogram.fsm.storage.base import DEFAULT_DESTINY
from aiogram.types import Message

from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.fsm import FilterEditFSM
from sophie_bot.modules.filters.handlers.filter_confirm import FilterConfirmHandler
from sophie_bot.modules.filters.types.modern_action_abc import (
    ActionSetupTryAgainException,
    ModernActionABC,
)
from sophie_bot.modules.filters.types.modern_action_data_types import (
    ACTION_DATA,
    ACTION_DATA_DUMPED,
)
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.utils_.base_handler import SophieMessageCallbackQueryHandler
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _


class ActionSetupConfirmHandler(SophieMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router):
        router.message.register(
            cls,
            FilterEditFSM.action_setup,
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    async def _filter_setup(self, filter_action: ModernActionABC) -> ACTION_DATA | None:
        if (
            isinstance(self.event, Message)
            and filter_action.interactive_setup
            and filter_action.interactive_setup.setup_confirm
        ):
            return await filter_action.interactive_setup.setup_confirm(self.event, self.data)
        else:
            return filter_action.default_data

    async def handle(self) -> Any:
        if not (
            filter_action_raw := (
                self.data.get("filter_action_setup") or await self.state.get_value("filter_action_setup")
            )
        ):
            raise SophieException("No filter action in state/data")

        filter_action = ALL_MODERN_ACTIONS[filter_action_raw]

        # TODO: Deal with typing below
        try:
            action_data_model: ACTION_DATA | None = await self._filter_setup(filter_action)
        except ActionSetupTryAgainException:
            return

        action_data: ACTION_DATA_DUMPED = action_data_model.model_dump(mode="json") if action_data_model else None

        # Add action to the list
        try:
            filter_item = await FilterInSetupType.get_filter(self.state, data=self.data)
        except ValueError:
            return await self.event.answer(_("Continuing setup is only possible by the same user who started it."))
        filter_item.actions[filter_action.name] = action_data
        await filter_item.set_filter_state(self.state)

        await self.state.set_state(DEFAULT_DESTINY)  # Reset to default state but do not flush the state data

        return await FilterConfirmHandler(self.event, **self.data)
