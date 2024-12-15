from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from stfu_tg import Italic, Section
from stfu_tg.doc import Element

from sophie_bot.db.models.notes import Saveable
from sophie_bot.modules.filters.handlers.confirm import ConfirmAddFilter
from sophie_bot.modules.filters.utils_.filter_abc import (
    FilterActionABC,
    FilterActionSetting,
    FilterActionSetupHandlerABC,
)
from sophie_bot.modules.notes.utils.parse import parse_saveable
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


class ReplyFilterConfirmHandler(FilterActionSetupHandlerABC):
    async def handle(self) -> Any:
        html_text: str = self.event.html_text
        self.data["filter_data"] = await parse_saveable(self.event, html_text)
        self.data["filter_action"] = ReplyFilterAction.name
        return await ConfirmAddFilter(self.event, **self.data)


class ReplyFilterAction(FilterActionABC[dict[str, Any]]):
    name = "reply"

    icon = "💭"
    title = l_("Reply to message")

    confirm_handler = ReplyFilterConfirmHandler

    settings = (
        FilterActionSetting(
            name_id="change_reply_text", title=l_("Change reply text"), icon="💬", handler=ReplyFilterConfirmHandler
        ),
    )

    @staticmethod
    def description(data: dict[str, Any]) -> Element | str:
        saveable = Saveable.model_validate(data)
        if saveable.text:
            return Section(Italic(saveable.text), title=_("Replies to the message with"), title_underline=False)

        return _("Replies to the message")

    @classmethod
    def setup_message(cls) -> tuple[Element | str, InlineKeyboardMarkup]:
        return _("Now, please type the text you want to automatically send."), InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=_("Markup help"), url="https://google.com")]]
        )

    @classmethod
    async def setup_confirm(cls, message: Message, data: dict[str, Any]) -> dict[str, Any]:
        return (await parse_saveable(message, message.html_text)).model_dump(mode="json")

    async def handle(self, message: Message, data: dict, filter_data: dict[str, Any]):
        pass
