from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.enums import ChatType
from aiogram.filters import Command

from korone.args import ArgumentSchema
from korone.db.models.chat import ChatModel
from korone.db.repositories.chat import ChatRepository, UserInGroupRepository
from korone.modules.users.args import UserArg
from korone.modules.utils_.admin import is_chat_creator, is_user_admin
from korone.modules.utils_.get_user import get_arg_or_reply_user
from korone.ui import Renderable, field, mention, section
from korone.utils.exception import KoroneError
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@dataclass(frozen=True, slots=True)
class UserInfoArguments:
    user: ChatModel | None = None


@flags.help(description=l_("Show detailed information about a user."))
@flags.disableable(name="info")
class UserInfoHandler(KoroneMessageHandler[UserInfoArguments]):
    arguments = ArgumentSchema(UserInfoArguments, user=UserArg(l_("User")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("info"),)

    async def handle(self) -> None:
        target_user: ChatModel | None = None
        try:
            selected_user = get_arg_or_reply_user(self.event, self.args.user)
        except KoroneError:
            selected_user = None

        if isinstance(selected_user, ChatModel):
            target_user = selected_user
        elif selected_user:
            target_user = await ChatRepository.get_by_chat_id(selected_user.id) or await ChatRepository.upsert_user(
                selected_user
            )
        elif self.event.from_user:
            target_user = await ChatRepository.get_by_chat_id(
                self.event.from_user.id
            ) or await ChatRepository.upsert_user(self.event.from_user)

        if not target_user:
            await self.answer(_("Could not identify user."))
            return

        chat_id = self.chat.chat_id
        user_id = target_user.id

        details: list[Renderable] = [
            field(_("ID"), target_user.chat_id),
            field(_("First Name"), target_user.first_name_or_title),
        ]

        if target_user.last_name:
            details.append(field(_("Last Name"), target_user.last_name))

        if target_user.username:
            details.append(field(_("Username"), f"@{target_user.username}"))

        display_name = target_user.first_name_or_title or "User"
        details.append(field(_("User Link"), mention(target_user.chat_id, display_name)))

        if self.chat.type != ChatType.PRIVATE:
            if await is_chat_creator(chat_id, user_id):
                details.append(_("This user is the owner of this chat."))
            elif await is_user_admin(chat_id, user_id):
                details.append(_("This user is an admin in this chat."))

        if not (self.event.from_user and target_user.chat_id == self.event.from_user.id):
            shared_chats_count = await UserInGroupRepository.count_user_groups(target_user.id)
            details.append(field(_("Shared Chats"), shared_chats_count))

        await self.answer(section(_("User Information"), *details))
