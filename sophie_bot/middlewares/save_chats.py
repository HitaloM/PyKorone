from typing import Any, Awaitable, Callable, Iterable, List, Optional

import structlog
from typing_extensions import override

from aiogram import BaseMiddleware
from aiogram.types import Chat, ChatMemberUpdated, Message, TelegramObject, Update, User

from sophie_bot.config import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.db.models.chat import ChatTopicModel, UserInGroupModel

logger = structlog.get_logger(__name__)


class SaveChatsMiddleware(BaseMiddleware):
    @staticmethod
    async def _delete_user_in_chat_by_user_id(user_id: int, group: ChatModel):
        logger.debug("SaveChatsMiddleware: Deleting user from chat", user_id=user_id, group=group)
        if not (user := await ChatModel.get_by_tid(user_id)):
            # not found - already deleted or didn't exist in a first place
            return

        if not (user_in_chat := await UserInGroupModel.ensure_delete(user, group)):
            return

        await user_in_chat.delete()

    @staticmethod
    async def _chats_update(chats: Iterable[Chat | User]):
        for chat in chats:
            logger.debug("SaveChatsMiddleware: Updating chat", chat_id=chat.id)
            if isinstance(chat, User):
                await ChatModel.upsert_user(chat)
            else:
                await ChatModel.upsert_group(chat)

    @staticmethod
    async def handle_replied_message(reply_message: Message, chat_id: int) -> List[Chat | User]:
        if reply_message.sender_chat and reply_message.sender_chat.id == chat_id:
            # Anonymous admin
            return []

        if reply_message.forum_topic_created:
            # Reply on a forum topic created message
            return []

        chats_to_update = []

        replied_message_user = reply_message.sender_chat or reply_message.from_user
        if replied_message_user and replied_message_user.id != CONFIG.bot_id:
            # Replied message user is not a bot
            chats_to_update.append(replied_message_user)

        # Reply to a forwarded message
        reply_to_forwarded = reply_message.forward_from_chat or reply_message.forward_from
        if reply_to_forwarded and reply_to_forwarded.id != CONFIG.bot_id:
            if reply_message.forward_from_chat:
                chats_to_update.append(reply_message.forward_from_chat)
            elif reply_message.forward_from:
                chats_to_update.append(reply_message.forward_from)

        return chats_to_update

    @staticmethod
    async def save_topic(message: Message, group: ChatModel):
        name: Optional[str]
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
            await ChatTopicModel.ensure_topic(group, message.message_thread_id, name)

    @staticmethod
    async def close_topic(message: Message, group_id: int):
        # TODO: Closed topics notation
        pass

    @staticmethod
    async def update_from_user(
        message: Message, current_group: ChatModel
    ) -> tuple[Optional[ChatModel], Optional[UserInGroupModel]]:
        if not message.from_user:
            return None, None

        if message.sender_chat and message.sender_chat.id == current_group.tid:
            return None, None

        if message.sender_chat:  # Sent as channel/group
            logger.debug("SaveChatsMiddleware: Updating from sender_chat", sender_chat=message.sender_chat.id)
            current_user = await ChatModel.upsert_group(message.sender_chat)
        else:
            logger.debug("SaveChatsMiddleware: Updating from from_user", from_user=message.from_user.id)
            current_user = await ChatModel.upsert_user(message.from_user)

        user_in_group = await UserInGroupModel.ensure_user_in_group(current_user, current_group)
        return current_user, user_in_group

    async def handle_message(self, message: Message, data: dict[str, Any]):
        logger.debug("SaveChatsMiddleware: Handling message", message_id=message.message_id, chat_id=message.chat.id)
        # Handle chat migrations
        # TODO: Make this update all data, so we won't need to call the next one
        if await self._handle_migration(data, message):
            return

        # Update current user and group
        chat, user = await self._handle_private_and_group_message(data, message)

        if message.chat.type not in ("group", "supergroup"):
            return

        # Update other users
        chats_to_update = await self._handle_message_update(message, chat)
        await self._chats_update(chats_to_update)
        data["updated_chats"] = chats_to_update

        # Forum topics
        await self.save_topic(message, chat)

        # New chat members
        data["new_users"] = await self._handle_new_chat_members(message, chat, user)

        # Left chat members
        await self._handle_left_chat_member(message, chat)

    @staticmethod
    async def _handle_migration(data: dict, message: Message):
        if message.migrate_from_chat_id:
            logger.debug(
                "SaveChatsMiddleware: Handling migration from chat",
                old_id=message.migrate_from_chat_id,
                new_id=message.chat.id,
            )
            data["chat_db"] = data["group_db"] = await ChatModel.do_chat_migrate(
                old_id=message.migrate_from_chat_id, new_chat=message.chat
            )
            return True
        elif message.migrate_to_chat_id:
            logger.debug(
                "SaveChatsMiddleware: Handling migration to chat",
                old_id=message.chat.id,
                new_id=message.migrate_to_chat_id,
            )
            return True
        else:
            return False

    async def _handle_private_and_group_message(self, data: dict, message: Message) -> tuple[ChatModel, ChatModel]:
        """Returns current group/chat model"""
        if message.chat.type == "private" and message.from_user:
            logger.debug("SaveChatsMiddleware: Handling private message", user_id=message.from_user.id)
            user = await ChatModel.upsert_user(message.from_user)
            data["chat_db"] = data["user_db"] = user
            return user, user
        else:
            logger.debug("SaveChatsMiddleware: Handling group message", chat_id=message.chat.id)
            current_group = await ChatModel.upsert_group(message.chat)
            data["chat_db"] = data["group_db"] = current_group

            current_user, data["user_in_group"] = await self.update_from_user(message, current_group)
            data["user_db"] = current_user

            return current_group, current_user or current_group

    async def _handle_message_update(self, message: Message, group: ChatModel):
        chats_to_update: list[Chat | User] = []

        if reply_message := message.reply_to_message:
            logger.debug(
                "SaveChatsMiddleware: Handling reply message update", reply_message_id=reply_message.message_id
            )
            chat_id = reply_message.chat.id
            await self.save_topic(reply_message, group)
            chats_to_update.extend(await self.handle_replied_message(reply_message, chat_id))

        elif message.forward_from or (message.forward_from_chat and message.forward_from_chat.id != group.tid):
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
            # Let's skip updating the user if it was already updated before in the _handle_message_update.
            if member.id == user_db.iid:
                continue

            logger.debug("SaveChatsMiddleware: Saving new chat member", user_id=member.id)
            new_user = await ChatModel.upsert_user(member)
            await UserInGroupModel.ensure_user_in_group(new_user, group)
            new_users.append(new_user)

        return new_users

    async def _handle_left_chat_member(self, message: Message, group: ChatModel):
        if not message.left_chat_member:
            return

        logger.debug("SaveChatsMiddleware: Handling left chat member", user_id=message.left_chat_member.id)
        if CONFIG.bot_id == message.left_chat_member.id:
            logger.debug("SaveChatsMiddleware: Bot left the chat", chat_id=group.tid)
            await group.delete_chat()
        else:
            await self._delete_user_in_chat_by_user_id(message.left_chat_member.id, group)

    @staticmethod
    async def save_from_user(data: dict):
        if not (from_user := data.get("event_from_user")):
            return

        logger.debug("SaveChatsMiddleware: Saving from user", user_id=from_user.id)
        user = await ChatModel.upsert_user(from_user)
        data["chat_db"] = data["user_db"] = user

    async def save_my_chat_member(self, event: ChatMemberUpdated) -> bool:
        status = event.new_chat_member.status
        logger.debug("SaveChatsMiddleware: Handling my_chat_member update", status=status, chat_id=event.chat.id)
        if status == "kicked":
            # Remove user, no need to further call handler
            if not (group := await ChatModel.get_by_tid(event.chat.id)):
                return False
            logger.debug("SaveChatsMiddleware: Bot was kicked from chat", chat_id=event.chat.id)
            await self._delete_user_in_chat_by_user_id(event.new_chat_member.user.id, group)
            return False
        elif status == "member":
            # Telegram will send a message event, so we'll handle it and save user later
            return False

        return True

    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        _continue = True
        if not isinstance(event, Update):
            return await handler(event, data)

        logger.debug("SaveChatsMiddleware: Incoming update", update_id=event.update_id)
        if event.message:
            await self.handle_message(event.message, data)
        elif any([event.callback_query, event.inline_query, event.poll_answer]):
            await self.save_from_user(data)
        elif event.my_chat_member:
            _continue = await self.save_my_chat_member(event.my_chat_member)

        return await handler(event, data) if _continue else None


#
# class SaveChatsChatMemberUpdatedMiddleware(SaveChatsMiddlewareABC):
#
#     async def __call__(self, handler: Callable[[ChatMemberUpdated, dict[str, Any]], Awaitable[Any]],
#                        event: ChatMemberUpdated, data: dict[str, Any]) -> Any:
#         user = await ChatModel.upsert_user(event.new_chat_member.user)
#         data['user_db'] = user
#         return await handler(event, data)
