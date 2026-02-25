from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import flags
from aiogram.enums import ChatType
from aiogram.filters import Command
from ass_tg.types import OptionalArg
from stfu_tg import Doc, KeyValue, Section, Title, UserLink

from korone.args.users import KoroneUserArg
from korone.db.repositories.chat import ChatRepository, UserInGroupRepository
from korone.modules.utils_.admin import is_chat_creator, is_user_admin
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric

    from korone.db.models.chat import ChatModel


@flags.help(description=l_("Shows the additional information about the user."))
@flags.disableable(name="info")
class UserInfoHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"user": OptionalArg(KoroneUserArg(l_("User")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("info"),)

    async def handle(self) -> None:
        target_user: ChatModel | None = self.data.get("user")
        if not target_user:
            reply_user = None
            if self.event.reply_to_message:
                reply_user = self.event.reply_to_message.from_user

            if reply_user:
                target_user = await ChatRepository.upsert_user(reply_user)
            else:
                user = getattr(self.event, "from_user", None)
                if user:
                    target_user = await ChatRepository.get_by_chat_id(user.id) or await ChatRepository.upsert_user(user)

        if not target_user:
            await self.event.reply(_("Could not identify user."))
            return

        chat_id = self.chat.chat_id
        user_id = target_user.id

        doc = Doc(Title(_("User Information")))

        doc += KeyValue(_("ID"), target_user.chat_id)
        doc += KeyValue(_("First Name"), target_user.first_name_or_title)

        if target_user.last_name:
            doc += KeyValue(_("Last Name"), target_user.last_name)

        if target_user.username:
            doc += KeyValue(_("Username"), f"@{target_user.username}")

        display_name = target_user.first_name_or_title or "User"
        doc += KeyValue(_("User Link"), UserLink(user_id=target_user.chat_id, name=display_name))

        doc += Section()

        if self.chat.type != ChatType.PRIVATE:
            if await is_chat_creator(chat_id, user_id):
                doc += _("This user is the owner of this chat.") + "\n"
            elif await is_user_admin(chat_id, user_id):
                doc += _("This user is an admin in this chat.") + "\n"

        if not (self.event.from_user and target_user.chat_id == self.event.from_user.id):
            shared_chats_count = await UserInGroupRepository.count_user_groups(target_user.id)
            doc += KeyValue(_("Shared Chats"), shared_chats_count)

        await self.event.reply(str(doc))
