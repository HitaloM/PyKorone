from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.enums import ChatType
from aiogram.filters import Command

from korone.args import ArgumentSchema
from korone.modules.users.args import UserArg
from korone.modules.utils_.message import is_real_reply
from korone.ui import Code, UIExpression, column, mention, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.db.models.chat import ChatModel


@dataclass(frozen=True, slots=True)
class ShowIDArguments:
    user: ChatModel | None = None


@flags.help(description=l_("Show user, chat, and topic IDs."))
@flags.disableable(name="id")
class ShowIDHandler(KoroneMessageHandler[ShowIDArguments]):
    arguments = ArgumentSchema(ShowIDArguments, user=UserArg(l_("User")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("id"),)

    async def handle(self) -> None:
        user = self.args.user

        items: list[UIExpression] = []

        if self.event.from_user:
            user_id = self.event.from_user.id
            items.append(template(_("Your ID: {id}"), id=Code(user_id)))

        if self.event.chat.type != ChatType.PRIVATE:
            items.append(template(_("Chat ID: {id}"), id=Code(self.event.chat.id)))

        if getattr(self.event, "message_thread_id", None) and self.event.chat.is_forum:
            items.append(template(_("Topic ID: {id}"), id=Code(self.event.message_thread_id)))

        if self.event.reply_to_message and is_real_reply(self.event) and self.event.reply_to_message.from_user:
            user_id = self.event.reply_to_message.from_user.id
            items.append(template(_("Replied user ID: {id}"), id=Code(user_id)))

        if user:
            user_id = user.chat_id
            items.append(
                template(_("{user}'s ID: {id}"), user=mention(user_id, user.first_name_or_title), id=Code(user_id))
            )

        await self.answer(column(*items))
