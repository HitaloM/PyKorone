from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.constants import TELEGRAM_ANONYMOUS_ADMIN_BOT_ID
from korone.db.repositories.chat import ChatRepository
from korone.db.repositories.chat_admin import ChatAdminRepository
from korone.filters.chat_status import GroupChatFilter
from korone.modules.utils_.admin import get_admins_rights
from korone.ui import UIExpression, bullets, column, mention, section, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("List visible administrators in the current chat."))
@flags.disableable(name="adminlist")
class AdminListHandler(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("adminlist", "admins"), GroupChatFilter(notify_on_fail=True))

    async def handle(self) -> None:
        chat_model = await ChatRepository.get_by_chat_id(self.chat.chat_id)
        if not chat_model:
            await self.answer(_("Chat not found."))
            return

        await get_admins_rights(chat_model.chat_id)
        admins = await ChatAdminRepository.get_chat_admins(chat_model)

        admin_items: list[UIExpression] = []
        for admin in admins:
            user_model = await ChatRepository.get_by_id(admin.user_id)
            if not user_model:
                continue

            if user_model.chat_id == TELEGRAM_ANONYMOUS_ADMIN_BOT_ID:
                continue

            admin_data = admin.data
            if admin_data.get("is_anonymous"):
                continue

            display_name = user_model.first_name_or_title or "User"
            admin_items.append(template(_("{user}"), user=mention(user_model.chat_id, display_name)))

        content = section(_("Admins"), bullets(*admin_items)) if admin_items else _("No visible admins found.")
        doc = column(template(_("Admins in {chat_name}"), chat_name=self.event.chat.title or self.chat.title), content)

        await self.answer(doc, disable_notification=True)
