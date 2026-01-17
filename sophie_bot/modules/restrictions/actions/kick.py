from typing import Optional

from aiogram.types import Message
from stfu_tg import Template, Title, UserLink
from stfu_tg.doc import Doc, Element

from sophie_bot.modules.filters.types.modern_action_abc import ModernActionABC
from sophie_bot.modules.legacy_modules.utils.restrictions import kick_user
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.utils.logger import log


class KickModernAction(ModernActionABC[None]):
    name = "kick_user"
    icon = "🚪"
    title = l_("Kick")
    as_flood = True

    @staticmethod
    def description(data: None) -> Element | str:
        return _("Kicks a user")

    async def handle(self, message: Message, data: dict, filter_data: None) -> Optional[Element]:
        if not message.from_user:
            return

        chat_id = message.chat.id
        user_id = message.from_user.id

        if await is_user_admin(chat_id, user_id):
            log.debug("KickModernAction: user is admin, skipping...")
            return

        doc = Doc(
            Title(_("Filter action")),
            Template(
                _("User {user} was automatically kicked based on a filter action"),
                user=UserLink(message.from_user.id, message.from_user.first_name),
            ),
        )

        if not await kick_user(chat_id, message.from_user.id):
            return

        return doc
