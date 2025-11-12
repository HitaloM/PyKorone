from typing import Any, Optional

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.fsm.storage.base import DEFAULT_DESTINY
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ass_tg.types import TextArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Doc, Section, Title

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.filters.callbacks import FilterActionCallback
from sophie_bot.modules.filters.fsm import FilterEditFSM
from sophie_bot.modules.filters.handlers.confirm import ConfirmAddFilter
from sophie_bot.modules.filters.utils_.filter_abc import (
    ALL_FILTER_ACTIONS,
    FilterActionABC,
)
from sophie_bot.modules.filters.utils_.legacy_filter_handler import text_legacy_handler_handles_on
from sophie_bot.modules.utils_.base_handler import (
    SophieCallbackQueryHandler,
    SophieMessageHandler,
)
from sophie_bot.modules.utils_.reply_or_edit import reply_or_edit
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


class AddFilterHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter(
                "addfilter",
            ),
            ~ChatTypeFilter("private"),
            UserRestricting(admin=True),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {"handler": TextArg(l_("Text to match"))}

    async def handle(self) -> Any:
        # TODO: Handler functions??
        filter_handler: str = self.data["handler"]

        # Set handler text to state data
        await self.state.update_data({"filter_handler": filter_handler})

        doc = Doc(
            Title(_("New filter")),
            # TODO: Filter handlers?
            Section(text_legacy_handler_handles_on(filter_handler), title=_("Handles")),
            " ",
            _("Select a filter action:"),
        )

        buttons = InlineKeyboardBuilder()

        for filter_action in ALL_FILTER_ACTIONS.values():
            buttons.row(
                InlineKeyboardButton(
                    text=f"{filter_action.icon} {filter_action.title}",
                    callback_data=FilterActionCallback(name=filter_action.name).pack(),
                )
            )

        buttons.row(InlineKeyboardButton(text=_("❌ Cancel"), callback_data="cancel"))

        await self.event.reply(str(doc), reply_markup=buttons.as_markup(), disable_web_page_preview=True)


class FilterActionClickHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return FilterActionCallback.filter(), ~ChatTypeFilter("private"), UserRestricting(admin=True)

    async def setup_message(self, filter_title: LazyProxy, text: LazyProxy | str, reply_markup: InlineKeyboardMarkup):
        # Set FSM state
        await self.state.set_state(FilterEditFSM.action_setup)

        doc = Doc(Title(f"{filter_title} {_('setup')}"), text)
        reply_markup.inline_keyboard.append(
            [
                InlineKeyboardButton(text=_("❌ Cancel"), callback_data="cancel"),
            ]
        )
        return await reply_or_edit(self.event, doc.to_html(), reply_markup=reply_markup)

    async def handle(self) -> Any:
        await self.check_for_message()
        data: FilterActionCallback = self.data["callback_data"]

        # Find that filter action
        filter_action = ALL_FILTER_ACTIONS[data.name]

        await self.state.update_data({"filter_action": data.name})
        self.data["filter_action"] = filter_action.name

        # If Filter has setup handler
        if setup_message := filter_action.setup_message():
            await self.setup_message(filter_action.title, *setup_message)
            return

        await FilterActionConfirmHandler(self.event, **self.data)


class FilterActionConfirmHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        # No admin verification to omit the possibility to stuck in the state if admin was removed in the middle of the process
        return FilterEditFSM.action_setup, ~ChatTypeFilter("private")

    async def handle(self) -> Any:
        filter_action_raw: Optional[str] = await self.state.get_value("filter_action")

        if not filter_action_raw:
            raise SophieException("No filter action in state")

        filter_action: FilterActionABC = ALL_FILTER_ACTIONS[filter_action_raw]

        state_data = await self.state.get_data()
        if "filters" not in state_data:
            state_data["filters"] = {}

        # Check
        if filter_action.name in state_data["filters"]:
            raise SophieException("Filter already exists")

        # Add new filter
        state_data["filters"][filter_action.name] = await filter_action.setup_confirm(self.event, self.data)

        await self.state.set_data(state_data)
        await self.state.set_state(DEFAULT_DESTINY)  # Reset to default state but do not flush the state data

        await ConfirmAddFilter(self.event, **self.data)
