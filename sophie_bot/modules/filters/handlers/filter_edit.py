from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import TextArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Code, Doc, Template

from sophie_bot.db.models import FiltersModel
from sophie_bot.db.models.filters import FilterInSetupType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.handlers.filter_confirm import FilterConfirmHandler
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Edits filter settings"))
class FilterEditHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter("editfilter"),
            UserRestricting(admin=True),
            GroupOrConnectedFilter(),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {
            "handler": TextArg(l_("Filter's keyword")),
        }

    async def handle(self) -> Any:
        keyword: str = self.data["handler"]

        # Find an item
        if not (filter_item := await FiltersModel.get_by_keyword(self.connection.tid, keyword)):
            return await self.event.reply(
                str(
                    Template(
                        _("Filter with handler {handler} can not be found! Check all filters using {cmd} command"),
                        handler=Code(keyword),
                        cmd=Code("/filters"),
                    )
                )
            )

        if filter_item.action:
            return await self.event.reply(
                Doc(
                    Template(_("Filter with handler {handler} can not be edited right now!"), handler=Code(keyword)),
                    _("The given filter was created before the filters update, and considered 'legacy'"),
                    _("Stay tuned for an update of Sophie."),
                    _("Alternatively you can delete this filter and create again."),
                ).to_html()
            )

        filter_in_setup = FilterInSetupType.from_model(filter_item)
        await filter_in_setup.set_filter_state(self.state)

        return await FilterConfirmHandler(self.event, **self.data).handle()
