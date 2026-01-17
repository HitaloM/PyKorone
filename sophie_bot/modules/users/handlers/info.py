from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import OptionalArg
from stfu_tg import Doc, KeyValue, Section, Title, UserLink

from sophie_bot.args.users import SophieUserArg
from sophie_bot.db.models import ChatModel
from sophie_bot.db.models.chat import UserInGroupModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Shows the additional information about the user."))
@flags.disableable(name="info")
@flags.args(user=OptionalArg(SophieUserArg(l_("User"))))
class UserInfoHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("info"),)

    async def handle(self) -> Any:
        # Fallback to self if no user provided
        target_user: ChatModel | None = self.data.get("user")
        if not target_user:
            # If no user arg, try to get self from event
            user = getattr(self.event, "from_user", None)
            if user:
                target_user = await ChatModel.get_or_create_user(user.id)

        if not target_user:
            await self.event.reply(_("Could not identify user."))
            return

        chat_tid = self.connection.tid
        user_tid = target_user.tid

        doc = Doc(Title(_("User Information")))

        doc += KeyValue(_("ID"), target_user.tid)
        doc += KeyValue(_("First Name"), target_user.first_name_or_title)

        if target_user.last_name:
            doc += KeyValue(_("Last Name"), target_user.last_name)

        if target_user.username:
            doc += KeyValue(_("Username"), f"@{target_user.username}")

        doc += KeyValue(
            _("User Link"),
            UserLink(user_id=target_user.tid, name=target_user.first_name_or_title),
        )

        doc += Section()

        if await is_user_admin(chat_tid, user_tid):
            doc += _("This user is an admin in this chat.") + "\n"

        # Count shared groups
        # We search for UserInGroupModel entries where the user is the target user
        shared_chats_count = await UserInGroupModel.find(UserInGroupModel.user.iid == target_user.iid).count()

        doc += KeyValue(_("Shared Chats"), shared_chats_count)

        await self.event.reply(str(doc))
