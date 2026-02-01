from __future__ import annotations

from typing import TYPE_CHECKING, override

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User

from korone.config import CONFIG
from korone.db.models.chat import ChatModel, UserInGroupModel
from korone.db.repositories import chat as chat_repo
from korone.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from aiogram.types import Chat, ChatMemberUpdated, Message

logger = get_logger(__name__)

type HandlerResult = TelegramObject | bool | None
type MiddlewareDataValue = (
    str
    | int
    | float
    | bool
    | TelegramObject
    | ChatModel
    | UserInGroupModel
    | list[TelegramObject]
    | list[ChatModel]
    | list[Chat | User]
    | dict[str, str | int | float | bool | None]
    | None
)
type MiddlewareData = dict[str, MiddlewareDataValue]


class SaveChatsMiddleware(BaseMiddleware):
    @staticmethod
    async def _delete_user_in_chat_by_user_id(user_id: int, group: ChatModel) -> None:
        logger.debug("SaveChatsMiddleware: Deleting user from chat", user_id=user_id, group=group)
        await chat_repo.delete_user_in_group(user_id, group)

    @staticmethod
    async def _chats_update(chats: Iterable[Chat | User]) -> None:
        for chat in chats:
            logger.debug("SaveChatsMiddleware: Updating chat", chat_id=chat.id)
            if isinstance(chat, User):
                await chat_repo.upsert_user(chat)
            else:
                await chat_repo.upsert_group(chat)

    @staticmethod
    async def handle_replied_message(reply_message: Message, chat_id: int) -> list[Chat | User]:
        if reply_message.sender_chat and reply_message.sender_chat.id == chat_id:
            return []

        if reply_message.forum_topic_created:
            return []

        chats_to_update = []

        replied_message_user = reply_message.sender_chat or reply_message.from_user
        if replied_message_user and replied_message_user.id != CONFIG.bot_id:
            chats_to_update.append(replied_message_user)

        reply_to_forwarded = reply_message.forward_from_chat or reply_message.forward_from
        if reply_to_forwarded and reply_to_forwarded.id != CONFIG.bot_id:
            if reply_message.forward_from_chat:
                chats_to_update.append(reply_message.forward_from_chat)
            elif reply_message.forward_from:
                chats_to_update.append(reply_message.forward_from)

        return chats_to_update

    @staticmethod
    async def save_topic(message: Message, group: ChatModel) -> None:
        name: str | None
        if message.forum_topic_created:
            name = message.forum_topic_created.name
        elif message.forum_topic_edited:
            name = message.forum_topic_edited.name
        elif message.is_topic_message:
            name = None
        else:
            return

        if message.message_thread_id is not None:
            logger.debug(
                "SaveChatsMiddleware: Saving topic", group=group, thread_id=message.message_thread_id, name=name
            )
            await chat_repo.ensure_topic(group, message.message_thread_id, name)

    @staticmethod
    async def close_topic(message: Message, group: ChatModel) -> None:
        if message.forum_topic_closed:
            logger.debug("SaveChatsMiddleware: Closing topic", group=group, thread_id=message.message_thread_id)
            if message.message_thread_id is not None:
                await chat_repo.ensure_topic(group, message.message_thread_id, None)

    @staticmethod
    async def update_from_user(
        message: Message, current_group: ChatModel
    ) -> tuple[ChatModel | None, UserInGroupModel | None]:
        if not message.from_user:
            return None, None

        if message.sender_chat and message.sender_chat.id == current_group.chat_id:
            return None, None

        if message.sender_chat:
            logger.debug("SaveChatsMiddleware: Updating from sender_chat", sender_chat=message.sender_chat.id)
            current_user = await chat_repo.upsert_group(message.sender_chat)
        else:
            logger.debug("SaveChatsMiddleware: Updating from from_user", from_user=message.from_user.id)
            current_user = await chat_repo.upsert_user(message.from_user)

        user_in_group = await chat_repo.ensure_user_in_group(current_user, current_group)
        return current_user, user_in_group

    async def handle_message(self, message: Message, data: MiddlewareData) -> None:
        logger.debug("SaveChatsMiddleware: Handling message", message_id=message.message_id, chat_id=message.chat.id)
        if await self._handle_migration(data, message):
            return

        chat, user = await self._handle_private_and_group_message(data, message)

        if message.chat.type not in {"group", "supergroup"}:
            return

        chats_to_update = await self._handle_message_update(message, chat)
        await self._chats_update(chats_to_update)
        data["updated_chats"] = chats_to_update

        await self.save_topic(message, chat)

        data["new_users"] = await self._handle_new_chat_members(message, chat, user)

        await self._handle_left_chat_member(message, chat)

    @staticmethod
    async def _handle_migration(data: MiddlewareData, message: Message) -> bool:
        if message.migrate_from_chat_id:
            logger.debug(
                "SaveChatsMiddleware: Handling migration from chat",
                old_id=message.migrate_from_chat_id,
                new_id=message.chat.id,
            )
            data["chat_db"] = data["group_db"] = await chat_repo.do_chat_migrate(
                old_id=message.migrate_from_chat_id, new_chat=message.chat
            )
            return True
        if message.migrate_to_chat_id:
            logger.debug(
                "SaveChatsMiddleware: Handling migration to chat",
                old_id=message.chat.id,
                new_id=message.migrate_to_chat_id,
            )
            return True
        return False

    async def _handle_private_and_group_message(
        self, data: MiddlewareData, message: Message
    ) -> tuple[ChatModel, ChatModel]:
        if message.chat.type == "private" and message.from_user:
            logger.debug("SaveChatsMiddleware: Handling private message", user_id=message.from_user.id)
            user = await chat_repo.upsert_user(message.from_user)
            data["chat_db"] = data["user_db"] = user
            return user, user
        logger.debug("SaveChatsMiddleware: Handling group message", chat_id=message.chat.id)
        current_group = await chat_repo.upsert_group(message.chat)
        data["chat_db"] = data["group_db"] = current_group

        current_user, data["user_in_group"] = await self.update_from_user(message, current_group)
        data["user_db"] = current_user

        return current_group, current_user or current_group

    async def _handle_message_update(self, message: Message, group: ChatModel) -> list[Chat | User]:
        chats_to_update: list[Chat | User] = []

        if reply_message := message.reply_to_message:
            logger.debug(
                "SaveChatsMiddleware: Handling reply message update", reply_message_id=reply_message.message_id
            )
            chat_id = reply_message.chat.id
            await self.save_topic(reply_message, group)
            chats_to_update.extend(await self.handle_replied_message(reply_message, chat_id))

        elif message.forward_from or (message.forward_from_chat and message.forward_from_chat.id != group.chat_id):
            logger.debug("SaveChatsMiddleware: Handling forwarded message update")
            if message.forward_from_chat:
                chats_to_update.append(message.forward_from_chat)
            elif message.forward_from:
                chats_to_update.append(message.forward_from)

        return chats_to_update

    @staticmethod
    async def _handle_new_chat_members(message: Message, group: ChatModel, user_db: ChatModel) -> list[ChatModel]:
        if not message.new_chat_members:
            return []

        logger.debug("SaveChatsMiddleware: Handling new chat members", members_count=len(message.new_chat_members))
        new_users = []
        for member in message.new_chat_members:
            if member.id == user_db.chat_id:
                continue

            logger.debug("SaveChatsMiddleware: Saving new chat member", user_id=member.id)
            new_user = await chat_repo.upsert_user(member)
            await chat_repo.ensure_user_in_group(new_user, group)
            new_users.append(new_user)

        return new_users

    async def _handle_left_chat_member(self, message: Message, group: ChatModel) -> None:
        if not message.left_chat_member:
            return

        logger.debug("SaveChatsMiddleware: Handling left chat member", user_id=message.left_chat_member.id)
        if CONFIG.bot_id == message.left_chat_member.id:
            logger.debug("SaveChatsMiddleware: Bot left the chat", chat_id=group.chat_id)
            await chat_repo.delete_chat(group)
        else:
            await self._delete_user_in_chat_by_user_id(message.left_chat_member.id, group)

    @staticmethod
    async def save_from_user(data: MiddlewareData) -> None:
        if not (from_user := data.get("event_from_user")):
            return
        if not isinstance(from_user, User):
            return

        logger.debug("SaveChatsMiddleware: Saving from user", user_id=from_user.id)
        user = await chat_repo.upsert_user(from_user)
        data["chat_db"] = data["user_db"] = user

    async def save_my_chat_member(self, event: ChatMemberUpdated) -> bool:
        status = event.new_chat_member.status
        logger.debug("SaveChatsMiddleware: Handling my_chat_member update", status=status, chat_id=event.chat.id)
        if status == "kicked":
            if not (group := await chat_repo.get_by_chat_id(event.chat.id)):
                return False
            logger.debug("SaveChatsMiddleware: Bot was kicked from chat", chat_id=event.chat.id)
            await self._delete_user_in_chat_by_user_id(event.new_chat_member.user.id, group)
            return False
        return status != "member"

    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, MiddlewareData], Awaitable[HandlerResult]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> HandlerResult:
        continue_ = True
        if not isinstance(event, Update):
            return await handler(event, data)

        logger.debug("SaveChatsMiddleware: Incoming update", update_id=event.update_id)
        if event.message:
            await self.handle_message(event.message, data)
        elif any([event.callback_query, event.inline_query, event.poll_answer]):
            await self.save_from_user(data)
        elif event.my_chat_member:
            continue_ = await self.save_my_chat_member(event.my_chat_member)

        return await handler(event, data) if continue_ else None
