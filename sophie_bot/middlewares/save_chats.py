from typing import Any, Awaitable, Callable, Iterable, List, Optional, Tuple

from aiogram import BaseMiddleware
from aiogram.types import Chat, ChatMemberUpdated, Message, Update, User

from sophie_bot import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.db.models.chat import UserInGroupModel, ChatTopicModel


class SaveChatsMiddleware(BaseMiddleware):
    @staticmethod
    async def _delete_user_in_chat_by_user_id(user_id: int, group_id: int):
        if not (user := await ChatModel.get_or_none(chat_id=user_id)):
            return
        if not (user_in_chat := await UserInGroupModel.get_or_none(user_id=user.id, group_id=group_id)):
            return
        await user_in_chat.delete()

    @staticmethod
    async def _chats_update(chats: Iterable[Chat | User]):
        if not chats:
            return

        await ChatModel.do_bulk_upsert(
            (ChatModel.get_user_model(x) if isinstance(x, User) else ChatModel.get_group_model(x) for x in chats)
        )

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
            chats_to_update.append(reply_message.forward_from_chat or reply_message.forward_from)

        return chats_to_update

    @staticmethod
    async def save_topic(message: Message, group_id: int):
        # if message.is_topic_message or message.forum_topic_created or message.forum_topic_edited:

        if message.forum_topic_created:
            name = message.forum_topic_created.name
        elif message.forum_topic_edited:
            name = message.forum_topic_edited.name
        elif message.is_topic_message:
            name = None
        else:
            return

        await ChatTopicModel.ensure_topic(group_id, message.message_thread_id, name)

    @staticmethod
    async def close_topic(message: Message, group_id: int):
        # TODO: Closed topics notation
        pass

    @staticmethod
    async def update_from_user(
            message: Message, chat_id: int, current_group: ChatModel
    ) -> Tuple[Optional[ChatModel], Optional[UserInGroupModel]]:
        if not message.from_user:
            return None, None

        if message.sender_chat and message.sender_chat.id == chat_id:
            return None, None

        if message.sender_chat:  # Sent as channel/group
            current_user = await ChatModel.upsert_group(message.sender_chat)
        else:
            current_user = await ChatModel.upsert_user(message.from_user)

        user_in_group = await UserInGroupModel.ensure_user_in_group(current_user.id, current_group.id)
        return current_user, user_in_group

    async def handle_message(self, message: Message, data: dict[str, Any]):
        # Handle chat migrations
        if await self._handle_migration(data, message):
            return

        chat = message.chat

        await self._handle_private_and_group_message(data, message, chat.id)

        group_id = data["chat_db"].id

        # Update other users
        chats_to_update = await self._handle_message_update(message, chat.id, group_id)

        # New chat members / removed chat member
        if chat.type in ("group", "supergroup"):
            await self._handle_member_updates(message, group_id)

        await self._chats_update(chats_to_update)

        data["updated_chats"] = chats_to_update

    @staticmethod
    async def _handle_migration(data: dict, message: Message):
        if message.migrate_from_chat_id or message.migrate_to_chat_id:
            if message.migrate_from_chat_id:
                data["chat_db"] = data["group_db"] = await ChatModel.do_chat_migrate(
                    old_id=message.migrate_from_chat_id, new_chat=message.chat
                )
            return True
        else:
            return False

    async def _handle_private_and_group_message(self, data: dict, message: Message, chat_id: int):
        if message.chat.type == "private" and message.from_user:
            user = (await ChatModel.upsert_user(message.from_user))
            data["chat_db"] = data["user_db"] = user
        else:
            current_group = (await ChatModel.upsert_group(message.chat))
            data["chat_db"] = data["group_db"] = current_group
            data["user_db"], data["user_in_group"] = await self.update_from_user(message, chat_id, current_group)

    async def _handle_message_update(self, message: Message, chat_id: int, group_id: int):
        chats_to_update = []

        # We skip forum_topic_created because we will add this one in the next if case.
        # Because replied message would have the name of the topic
        if message.is_topic_message and not message.forum_topic_created:
            await self.save_topic(message, group_id)

        if reply_message := message.reply_to_message:
            chat_id = reply_message.chat.id
            await self.save_topic(message.reply_to_message, group_id)
            chats_to_update.extend(await self.handle_replied_message(reply_message, chat_id))

        elif message.forward_from or (message.forward_from_chat and message.forward_from_chat.id != chat_id):
            chats_to_update.append(message.forward_from_chat or message.forward_from)

        elif message.forum_topic_created:
            await self.save_topic(message, group_id)

        elif message.forum_topic_edited:
            await self.save_topic(message, group_id)

        elif message.forum_topic_closed:
            await self.close_topic(message, group_id)

        return chats_to_update

    async def _handle_member_updates(self, message: Message, group_id: int):
        if message.new_chat_members:
            for member in message.new_chat_members:
                new_user = (await ChatModel.upsert_user(member))[0]
                await UserInGroupModel.ensure_user_in_group(new_user.id, group_id)
        elif message.left_chat_member:
            if CONFIG.bot_id == message.left_chat_member.id:
                await ChatModel.do_chat_delete(group_id)
            else:
                await self._delete_user_in_chat_by_user_id(message.left_chat_member.id, group_id)

    @staticmethod
    async def save_from_user(data: dict):
        if not (from_user := data.get("event_from_user")):
            return

        user = (await ChatModel.upsert_user(from_user))[0]
        data["chat_db"] = data["user_db"] = user

    async def save_my_chat_member(self, event: ChatMemberUpdated) -> bool:
        status = event.new_chat_member.status
        if status == "kicked":
            # Remove user, no need to further call handler
            if not (group := await ChatModel.get_or_none(chat_id=event.chat.id)):
                return False
            await self._delete_user_in_chat_by_user_id(event.new_chat_member.user.id, group.id)
            return False
        elif status == "member":
            # Telegram will send a message event, so we'll handle it and save user later
            return False

        return True

    async def __call__(
            self, handler: Callable[[Update, dict[str, Any]], Awaitable[Any]], update: Update, data: dict[str, Any]
    ) -> Any:
        _continue = True
        if update.message:
            await self.handle_message(update.message, data)
        elif any([update.callback_query, update.inline_query, update.poll_answer]):
            await self.save_from_user(data)
        elif update.my_chat_member:
            _continue = await self.save_my_chat_member(update.my_chat_member)

        return await handler(update, data) if _continue else None

#
# class SaveChatsChatMemberUpdatedMiddleware(SaveChatsMiddlewareABC):
#
#     async def __call__(self, handler: Callable[[ChatMemberUpdated, dict[str, Any]], Awaitable[Any]],
#                        event: ChatMemberUpdated, data: dict[str, Any]) -> Any:
#         user = await ChatModel.upsert_user(event.new_chat_member.user)
#         data['user_db'] = user
#         return await handler(event, data)
