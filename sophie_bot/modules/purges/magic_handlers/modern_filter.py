from aiogram.types import Message
from stfu_tg.doc import Element

from sophie_bot.modules.filters.types.modern_action_abc import (
    ModernActionABC,
    ModernActionSetting,
)
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.utils.logger import log


class DelMsgModernModern(ModernActionABC[None]):
    name = "delmsg"

    icon = "🗑"
    title = l_("Delete the message")

    default_data = None

    @staticmethod
    def description(data: None) -> Element | str:
        return _("Deletes the message")

    def settings(self, data: None) -> dict[str, ModernActionSetting]:
        return {}
        # return (
        # ModernActionSetting(
        #     name_id="delmsg_allow_admins",
        #     title=l_("Allow deleting admins messages"),
        #     icon="🗑",
        # ),
        # )

    async def handle(self, message: Message, data: dict, filter_data: None):
        if not message.from_user:
            return

        if await is_user_admin(message.chat.id, message.from_user.id):
            log.debug("DelMsgModernModern: user is admin, skipping!")
            return

        await common_try(message.delete())
