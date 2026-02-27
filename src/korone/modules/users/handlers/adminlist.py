from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command
from stfu_tg import Doc, Section, Template, Title, UserLink, VList

from korone.constants import TELEGRAM_ANONYMOUS_ADMIN_BOT_ID
from korone.db.repositories.chat import ChatRepository
from korone.db.repositories.chat_admin import ChatAdminRepository
from korone.filters.chat_status import GroupChatFilter
from korone.modules.utils_.admin import get_admins_rights
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from stfu_tg.doc import Element


@flags.help(description=l_("List visible administrators in the current chat."))
@flags.disableable(name="adminlist")
class AdminListHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("adminlist", "admins"), GroupChatFilter(notify_on_fail=True))

    async def handle(self) -> None:
        chat_model = await ChatRepository.get_by_chat_id(self.chat.chat_id)
        if not chat_model:
            await self.event.reply(_("Chat not found."))
            return

        await get_admins_rights(chat_model.chat_id)
        admins = await ChatAdminRepository.get_chat_admins(chat_model)

        doc = Doc(Title(Template(_("Admins in {chat_name}"), chat_name=self.event.chat.title)))

        admin_items: list[Element] = []
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
            admin_items.append(Template(_("{user}"), user=UserLink(user_model.chat_id, display_name)))

        if not admin_items:
            doc += _("No visible admins found.")
        else:
            doc += Section(VList(*admin_items), title=_("Admins"))

        await self.event.reply(str(doc), disable_notification=True)
