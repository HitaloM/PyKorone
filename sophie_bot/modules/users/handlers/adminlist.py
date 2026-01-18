from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Doc, Title, UserLink

from sophie_bot.constants import TELEGRAM_ANONYMOUS_ADMIN_BOT_ID
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_admin import ChatAdminModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Lists all the chats admins."))
@flags.disableable(name="adminlist")
class AdminListHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("adminlist", "admins")),)

    async def handle(self) -> Any:
        if self.event.chat.type == "private":
            return await self.event.reply(_("This command can only be used in groups."))

        chat_model = await ChatModel.get_by_tid(self.connection.tid)
        if not chat_model:
            return await self.event.reply(_("Chat not found."))

        # Fetch admins from DB
        # Note: ChatAdminModel stores admins. We need to fetch them.
        # This mirrors the legacy behavior but uses the new DB structure.

        admins_cursor = ChatAdminModel.find(ChatAdminModel.chat.id == chat_model.iid)  # type: ignore
        admins = await admins_cursor.to_list()

        doc = Doc(Title(_("Admins in {chat_name}").format(chat_name=self.event.chat.title)))

        if not admins:
            # Fallback or check live if DB is empty?
            # Usually admin cache should be populated.
            # For now, let's assume it works or returns "No admins found" which is technically impossible for a group unless anon.
            pass

        count = 0
        for admin_entry in admins:
            # We need to fetch the user details. ChatAdminModel links to User (ChatModel).
            # admin_entry.user is a Link. We need to fetch it if not automatically fetched (Beanie usually requires fetch).

            # Optimization: If ChatAdminModel definition doesn't auto-fetch, we might need to agg or fetch separately.
            # Assuming standard Beanie Link behavior or fetching explicitly.

            # Let's try to fetch the user model.
            user = await ChatModel.get_by_iid(admin_entry.user.id)
            if not user:
                continue

            # Skip anonymous admin bot if desired, or keep it. Legacy skipped "anonymous" rights but here we check user ID.
            if user.tid == TELEGRAM_ANONYMOUS_ADMIN_BOT_ID:
                continue

            # Check if anonymous admin
            if admin_entry.member.is_anonymous:
                continue

            doc += f"- {UserLink(user.tid, user.first_name_or_title)} ({user.tid})"
            count += 1

        if count == 0:
            doc += _("No visible admins found.")

        await self.event.reply(str(doc), disable_notification=True)
