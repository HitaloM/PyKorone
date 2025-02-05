from typing import Any, Optional

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from stfu_tg import Bold, Doc, Italic, PreformattedHTML, Section, Template, Title
from stfu_tg.doc import Element

from sophie_bot.db.models.notes import Saveable
from sophie_bot.modules.filters.types.modern_action_abc import (
    ActionSetupMessage,
    ModernActionABC,
    ModernActionSetting,
)
from sophie_bot.modules.notes.utils.parse import parse_saveable
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


async def set_reply_text(event: Message | CallbackQuery, data: dict[str, Any]) -> Saveable:
    if isinstance(event, CallbackQuery):
        raise ValueError("This handlers setup_confirm can only be used with messages")

    return await parse_saveable(event, event.html_text)


async def reply_action_setup_message(_event: Message | CallbackQuery, _data: dict[str, Any]) -> ActionSetupMessage:
    return ActionSetupMessage(
        text=_("Now, please type the text you want to automatically send."),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=_("Markup help"), url="https://google.com")]]
        ),
    )


class ReplyModernAction(ModernActionABC[Saveable]):
    name = "reply"

    icon = "💭"
    title = l_("Reply to message")

    interactive_setup = ModernActionSetting(
        title=l_("Reply to message"), setup_message=reply_action_setup_message, setup_confirm=set_reply_text
    )
    data_object = Saveable

    @staticmethod
    def description(data: Saveable) -> Element | str:
        if data.text:
            return Section(Italic(data.text), title=_("Replies to the message with"), title_underline=False)

        return _("Replies to the message")

    def settings(self, data: Saveable) -> dict[str, ModernActionSetting]:
        return {
            "reply_text": ModernActionSetting(
                title=l_("Change reply text"),
                icon="💬",
                setup_message=reply_action_setup_message,
                setup_confirm=set_reply_text,
            ),
        }

    async def handle(self, message: Message, data: dict, filter_data: Saveable) -> Optional[Element]:
        title = Bold(Title(Template("🪄 {text}", text=_("Reply"))))

        if filter_data.buttons or filter_data.file:
            # We have to send the note separately
            return await common_try(
                send_saveable(
                    message,
                    message.chat.id,
                    filter_data,
                    title=title,
                    reply_to=message.message_id,
                )
            )

        return Doc(
            title,
            PreformattedHTML(filter_data.text),
        )
