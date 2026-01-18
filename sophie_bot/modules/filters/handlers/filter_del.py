from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import IntArg, TextArg
from ass_tg.types.base_abc import ArgFabric
from ass_tg.types.logic import OptionalArg
from stfu_tg import Code, Doc, KeyValue, Section, Template

from sophie_bot.db.models import FiltersModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.is_connected import GroupOrConnectedFilter
from sophie_bot.modules.filters.utils_.filter_action_text import filter_action_text
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(
    description=l_("Deletes a filter"),
    args={"handler": TextArg(l_("Text to match"))},  # hide index arg
)
class FilterDeleteHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter("delfilter"),
            GroupOrConnectedFilter(),
            UserRestricting(admin=True),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {
            "index": OptionalArg(IntArg(l_("?Filter index"))),
            "handler": TextArg(l_("Text to match")),
        }

    async def _many_filters_message(self, keyword: str, items: list[FiltersModel]):
        return await self.event.reply(
            Doc(
                Template(_("There are multiple filters with keyword {keyword}!"), keyword=Code(keyword)),
                Section(
                    *(
                        KeyValue(i + 1, filter_action_text(item.action, list(item.actions.keys())), suffix=" -> ")
                        for i, item in enumerate(items)
                    ),
                    title=_("Filters"),
                ),
                Template(
                    _("Please specify the filter index using {cmd} command."), cmd=Code(f"/delfilter <index> {keyword}")
                ),
                Template(_("For example: {cmd}"), cmd=Code(f"/delfilter {len(items)} {keyword}")),
            ).to_html()
        )

    async def handle(self) -> Any:
        keyword: str = self.data["handler"]
        index: int = (self.data["index"] or 1) - 1

        if not (items := await FiltersModel.get_legacy_by_keyword(self.connection.tid, keyword)):
            return await self.event.reply(
                Doc(
                    Template(_("The filter with keyword {keyword} does not exist!"), keyword=Code(keyword)),
                    Template(_("Please check the available filters using {cmd} command."), cmd="/filters"),
                ).to_html()
            )

        if len(items) > 1 and not index:
            return await self._many_filters_message(keyword, items)

        await items[index].delete()

        return await self.event.reply(
            Template(_("🗑 The filter with keyword {keyword} was deleted!"), keyword=Code(keyword)).to_html(),
        )
