from typing import Any, Optional

from aiogram.types import CallbackQuery, Message
from pydantic import BaseModel
from stfu_tg import Section
from stfu_tg.doc import Element

from sophie_bot.modules.filters.types.modern_action_abc import (
    ActionSetupMessage,
    ModernActionABC,
    ModernActionSetting,
)
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.modules.warns.utils import warn_user
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


class WarnActionDataModel(BaseModel):
    reason: Optional[str]


async def setup_confirm(event: Message | CallbackQuery, data: dict[str, Any]) -> WarnActionDataModel:
    if isinstance(event, CallbackQuery):
        raise ValueError("This handlers setup_confirm can only be used with messages")

    reason = event.text or None

    return WarnActionDataModel(reason=reason)


async def setup_message(_event: Message | CallbackQuery, _data: dict[str, Any]) -> ActionSetupMessage:
    return ActionSetupMessage(
        text=_("Please write the warn reason."),
    )


class WarnModernAction(ModernActionABC[WarnActionDataModel]):
    name = "warn_user"

    icon = "⚠️"
    title = l_("Warn")
    data_object = WarnActionDataModel
    default_data = WarnActionDataModel(reason=None)

    @staticmethod
    def description(data: WarnActionDataModel) -> Element | str:
        if data.reason:
            # TODO: not en_US
            return Section(data.reason, title=_("Warn user with the reason"), title_underline=False)

        return _("Warns user with no reason")

    def settings(self, data: WarnActionDataModel) -> dict[str, ModernActionSetting]:
        return {
            "change_warn_reason": ModernActionSetting(
                title=l_("Change warn reason"),
                icon="📝",
                setup_message=setup_message,
                setup_confirm=setup_confirm,
            ),
        }

    async def handle(self, message: Message, data: dict, filter_data: WarnActionDataModel):
        if not message.from_user:
            return

        chat_id = message.chat.id
        target_user = message.from_user.id

        if await is_user_admin(chat_id, target_user):
            return

        text = filter_data.reason or _("No reason")

        # Legacy workaround
        # connected_chat = await get_connected_chat(message)

        await warn_user(message.chat, message.from_user, message.from_user, text)
