from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from bson import ObjectId
from stfu_tg import Code, Template

from sophie_bot.db.models import FiltersModel
from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.logging.events import LogEvent
from sophie_bot.modules.logging.utils import log_event
from sophie_bot.modules.filters.callbacks import SaveFilterCallback
from sophie_bot.modules.filters.utils_.legacy_filter_handler import (
    check_legacy_filter_handler,
)
from sophie_bot.utils.handlers import SophieCallbackQueryHandler
from sophie_bot.utils.i18n import gettext as _


class FilterSaveHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            SaveFilterCallback.filter(),
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    async def save_filter(self, filter_setup: FilterInSetupType):
        # Update instead of save
        if filter_setup.oid:
            filter_model = await FiltersModel.get_by_id(ObjectId(filter_setup.oid))
            await filter_model.update_fields(filter_setup)
            await filter_model.save()
        else:
            filter_model = filter_setup.to_model(self.connection.tid)
            await filter_model.save()

        await log_event(
            self.connection.tid,
            self.event.from_user.id,
            LogEvent.FILTER_SAVED,
            {"keyword": filter_setup.handler.keyword},
        )

    async def handle(self) -> Any:
        try:
            filter_item: FilterInSetupType = await FilterInSetupType.get_filter(self.state)
        except ValueError:
            return await self.event.answer(_("Continuing setup is only possible by the same user who started it."))

        # Check
        await check_legacy_filter_handler(self.event, filter_item.handler.keyword, self.connection, filter_item.oid)

        await self.save_filter(filter_item)

        doc = Template(_("Filter on {keyword} was saved."), keyword=Code(filter_item.handler.keyword))

        return await self.edit_text(doc.to_html())
