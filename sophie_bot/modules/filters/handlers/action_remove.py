from typing import Any

from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.callbacks import RemoveFilterActionCallback
from sophie_bot.modules.filters.handlers.filter_confirm import FilterConfirmHandler
from sophie_bot.utils.handlers import SophieCallbackQueryHandler
from sophie_bot.utils.i18n import gettext as _


class ActionRemoveHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            RemoveFilterActionCallback.filter(),
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    async def handle(self) -> Any:
        data: RemoveFilterActionCallback = self.data["callback_data"]
        try:
            filter_item = await FilterInSetupType.get_filter(self.state, data=self.data)
        except ValueError:
            return await self.event.answer(_("Continuing setup is only possible by the same user who started it."))

        filter_item.actions.pop(data.name)

        await filter_item.set_filter_state(self.state)
        return await FilterConfirmHandler(self.event, **self.data)
