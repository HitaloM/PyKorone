from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from aiogram import BaseMiddleware
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Chat, Update, User
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.config import CONFIG
from korone.db.repositories.chat import ChatRepository
from korone.logger import get_logger
from korone.middlewares.context_data import as_korone_context
from korone.modules.help.callbacks import HELP_START_PAYLOAD
from korone.modules.utils_.chat_member import update_chat_members
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

    from aiogram.types import ChatJoinRequest, ChatMemberUpdated, Message, TelegramObject

    from korone.db.models.chat import ChatModel, UserInGroupModel

logger = get_logger(__name__)


class SaveChatsMiddleware(BaseMiddleware):
    @staticmethod
    async def _delete_user_in_chat_by_user_id(user_id: int, group: ChatModel) -> None:
        await logger.adebug("SaveChatsMiddleware: Deleting user from chat", user_id=user_id, group=group)
        await ChatRepository.delete_user_in_group(user_id, group)

    @staticmethod
    async def _chats_update(chats: Iterable[Chat | User]) -> None:
        for chat in chats:
            await logger.adebug("SaveChatsMiddleware: Updating chat", chat_id=chat.id)
            if isinstance(chat, User):
                await ChatRepository.upsert_user(chat)
            else:
                await ChatRepository.upsert_group(chat)

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
            await logger.adebug(
                "SaveChatsMiddleware: Saving topic", group=group, thread_id=message.message_thread_id, name=name
            )
            await ChatRepository.ensure_topic(group, message.message_thread_id, name)

    @staticmethod
    async def close_topic(message: Message, group: ChatModel) -> None:
        if message.forum_topic_closed:
            await logger.adebug("SaveChatsMiddleware: Closing topic", group=group, thread_id=message.message_thread_id)
            if message.message_thread_id is not None:
                await ChatRepository.ensure_topic(group, message.message_thread_id, None)

    @staticmethod
    async def update_from_user(
        message: Message, current_group: ChatModel
    ) -> tuple[ChatModel | None, UserInGroupModel | None]:
        if not message.from_user:
            return None, None

        if message.sender_chat and message.sender_chat.id == current_group.chat_id:
            return None, None

        if message.sender_chat:
            await logger.adebug("SaveChatsMiddleware: Updating from sender_chat", sender_chat=message.sender_chat.id)
            current_user = await ChatRepository.upsert_group(message.sender_chat)
        else:
            await logger.adebug("SaveChatsMiddleware: Updating from from_user", from_user=message.from_user.id)
            current_user = await ChatRepository.upsert_user(message.from_user)

        user_in_group = await ChatRepository.ensure_user_in_group(current_user, current_group)
        return current_user, user_in_group

    async def handle_message(self, message: Message, data: dict[str, Any]) -> None:
        context = as_korone_context(data)
        await logger.adebug(
            "SaveChatsMiddleware: Handling message", message_id=message.message_id, chat_id=message.chat.id
        )
        if await self._handle_migration(data, message):
            return

        chat, user = await self._handle_private_and_group_message(data, message)

        if message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
            return

        chats_to_update = await self._handle_message_update(message, chat)
        await self._chats_update(chats_to_update)
        context["updated_chats"] = chats_to_update

        await self.save_topic(message, chat)

        context["new_users"] = await self._handle_new_chat_members(message, chat, user)

        await self._handle_left_chat_member(message, chat)
        await self._handle_chat_owner_updates(message, chat)

    @staticmethod
    async def _handle_migration(data: dict[str, Any], message: Message) -> bool:
        context = as_korone_context(data)
        if message.migrate_from_chat_id:
            await logger.adebug(
                "SaveChatsMiddleware: Handling migration from chat",
                old_id=message.migrate_from_chat_id,
                new_id=message.chat.id,
            )
            context["chat_db"] = context["group_db"] = await ChatRepository.do_chat_migrate(
                old_id=message.migrate_from_chat_id, new_chat=message.chat
            )
            return True
        if message.migrate_to_chat_id:
            await logger.adebug(
                "SaveChatsMiddleware: Handling migration to chat",
                old_id=message.chat.id,
                new_id=message.migrate_to_chat_id,
            )
            current_group = await ChatRepository.upsert_group(message.chat)
            context["chat_db"] = context["group_db"] = current_group
            return True
        return False

    async def _handle_private_and_group_message(
        self, data: dict[str, Any], message: Message
    ) -> tuple[ChatModel, ChatModel]:
        context = as_korone_context(data)
        if message.chat.type == ChatType.PRIVATE and message.from_user:
            await logger.adebug("SaveChatsMiddleware: Handling private message", user_id=message.from_user.id)
            user = await ChatRepository.upsert_user(message.from_user)
            context["chat_db"] = context["user_db"] = user
            return user, user
        await logger.adebug("SaveChatsMiddleware: Handling group message", chat_id=message.chat.id)
        current_group = await ChatRepository.upsert_group(message.chat)
        context["chat_db"] = context["group_db"] = current_group

        current_user, user_in_group = await self.update_from_user(message, current_group)
        context["user_in_group"] = user_in_group
        context["user_db"] = current_user

        return current_group, current_user or current_group

    async def _handle_message_update(self, message: Message, group: ChatModel) -> list[Chat | User]:
        chats_to_update: list[Chat | User] = []

        if reply_message := message.reply_to_message:
            await logger.adebug(
                "SaveChatsMiddleware: Handling reply message update", reply_message_id=reply_message.message_id
            )
            chat_id = reply_message.chat.id
            await self.save_topic(reply_message, group)
            chats_to_update.extend(await self.handle_replied_message(reply_message, chat_id))

        elif message.forward_from or (message.forward_from_chat and message.forward_from_chat.id != group.chat_id):
            await logger.adebug("SaveChatsMiddleware: Handling forwarded message update")
            if message.forward_from_chat:
                chats_to_update.append(message.forward_from_chat)
            elif message.forward_from:
                chats_to_update.append(message.forward_from)

        return chats_to_update

    @staticmethod
    async def _handle_new_chat_members(message: Message, group: ChatModel, user_db: ChatModel) -> list[ChatModel]:
        if not message.new_chat_members:
            return []

        await logger.adebug(
            "SaveChatsMiddleware: Handling new chat members", members_count=len(message.new_chat_members)
        )
        new_users = []
        for member in message.new_chat_members:
            if member.id == user_db.chat_id:
                continue

            await logger.adebug("SaveChatsMiddleware: Saving new chat member", user_id=member.id)
            new_user = await ChatRepository.upsert_user(member)
            await ChatRepository.ensure_user_in_group(new_user, group)
            new_users.append(new_user)

        return new_users

    async def _handle_left_chat_member(self, message: Message, group: ChatModel) -> None:
        if not message.left_chat_member:
            return

        await logger.adebug("SaveChatsMiddleware: Handling left chat member", user_id=message.left_chat_member.id)
        if CONFIG.bot_id == message.left_chat_member.id:
            await logger.adebug("SaveChatsMiddleware: Bot left the chat", chat_id=group.chat_id)
            await ChatRepository.delete_chat(group)
        else:
            await self._delete_user_in_chat_by_user_id(message.left_chat_member.id, group)

    @staticmethod
    async def _refresh_admin_cache(group: ChatModel, *, reason: str) -> None:
        await logger.adebug(
            "SaveChatsMiddleware: Refreshing admin cache after ownership update", chat_id=group.chat_id, reason=reason
        )
        try:
            await update_chat_members(group)
        except TelegramAPIError as error:
            await logger.awarning(
                "SaveChatsMiddleware: Failed to refresh admin cache after ownership update",
                chat_id=group.chat_id,
                reason=reason,
                error=str(error),
            )

    async def _handle_chat_owner_updates(self, message: Message, group: ChatModel) -> None:
        if owner_changed := message.chat_owner_changed:
            new_owner = owner_changed.new_owner
            await logger.adebug(
                "SaveChatsMiddleware: Handling chat owner changed",
                chat_id=group.chat_id,
                new_owner_user_id=new_owner.id,
            )
            new_owner_db = await ChatRepository.upsert_user(new_owner)
            await ChatRepository.ensure_user_in_group(new_owner_db, group)
            await self._refresh_admin_cache(group, reason="chat_owner_changed")
            return

        if not (owner_left := message.chat_owner_left):
            return

        new_owner = owner_left.new_owner
        await logger.adebug(
            "SaveChatsMiddleware: Handling chat owner left",
            chat_id=group.chat_id,
            old_owner_user_id=message.from_user.id if message.from_user else None,
            new_owner_user_id=new_owner.id if new_owner else None,
        )

        if message.from_user and message.from_user.id != CONFIG.bot_id:
            await self._delete_user_in_chat_by_user_id(message.from_user.id, group)

        if new_owner:
            new_owner_db = await ChatRepository.upsert_user(new_owner)
            await ChatRepository.ensure_user_in_group(new_owner_db, group)

        await self._refresh_admin_cache(group, reason="chat_owner_left")

    @staticmethod
    async def save_from_user(data: dict[str, Any]) -> None:
        context = as_korone_context(data)
        from_user = context.get("event_from_user")
        if not isinstance(from_user, User):
            return

        await logger.adebug("SaveChatsMiddleware: Saving from user", user_id=from_user.id)
        user = await ChatRepository.upsert_user(from_user)
        context["user_db"] = user

        event_chat = context.get("event_chat")
        if isinstance(event_chat, Chat):
            chat_type = ChatType(event_chat.type)
            if chat_type in {ChatType.GROUP, ChatType.SUPERGROUP}:
                await logger.adebug("SaveChatsMiddleware: Saving callback event chat", chat_id=event_chat.id)
                group = await ChatRepository.upsert_group(event_chat)
                context["chat_db"] = context["group_db"] = group
                context["user_in_group"] = await ChatRepository.ensure_user_in_group(user, group)
                return

        context["chat_db"] = context["user_db"] = user

    @staticmethod
    async def save_chat_join_request(join_request: ChatJoinRequest, data: dict[str, Any]) -> None:
        context = as_korone_context(data)
        await logger.adebug(
            "SaveChatsMiddleware: Saving chat join request",
            chat_id=join_request.chat.id,
            user_id=join_request.from_user.id,
        )
        chat = await ChatRepository.upsert_group(join_request.chat)
        user = await ChatRepository.upsert_user(join_request.from_user)
        context["chat_db"] = context["group_db"] = chat
        context["user_db"] = user

    @staticmethod
    async def _send_group_welcome_message(event: ChatMemberUpdated) -> None:
        if event.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
            return

        bot = event.bot
        if bot is None:
            await logger.awarning(
                "SaveChatsMiddleware: Bot instance unavailable while sending welcome message", chat_id=event.chat.id
            )
            return

        help_url = await create_start_link(bot, HELP_START_PAYLOAD)
        buttons = InlineKeyboardBuilder()
        buttons.button(text=f"ℹ️ {_('Help')}", url=help_url)
        buttons.button(text=_("📢 Channel"), url=CONFIG.news_channel)
        buttons.adjust(2)

        text = _(
            "Hi, I'm Korone, your all-in-one bot for this chat. Use the buttons below to open help and follow updates."
        )

        try:
            await bot.send_message(chat_id=event.chat.id, text=str(text), reply_markup=buttons.as_markup())
        except TelegramAPIError as error:
            await logger.awarning(
                "SaveChatsMiddleware: Failed to send group welcome message", chat_id=event.chat.id, error=str(error)
            )

    @classmethod
    async def save_my_chat_member(cls, event: ChatMemberUpdated) -> bool:
        old_status = event.old_chat_member.status
        status = event.new_chat_member.status
        await logger.adebug(
            "SaveChatsMiddleware: Handling my_chat_member update",
            status=status,
            old_status=old_status,
            chat_id=event.chat.id,
        )
        if status in {ChatMemberStatus.KICKED, ChatMemberStatus.LEFT}:
            if not (group := await ChatRepository.get_by_chat_id(event.chat.id)):
                return False
            await logger.adebug("SaveChatsMiddleware: Bot left chat", chat_id=event.chat.id, status=status)
            await ChatRepository.delete_chat(group)
            return False

        if status == ChatMemberStatus.RESTRICTED:
            can_send_messages = getattr(event.new_chat_member, "can_send_messages", True)
            if can_send_messages is False:
                await logger.awarning(
                    "SaveChatsMiddleware: Bot restricted from sending messages, leaving chat", chat_id=event.chat.id
                )
                try:
                    await event.bot.leave_chat(event.chat.id)  # pyright: ignore[reportOptionalMemberAccess]
                    await logger.ainfo("SaveChatsMiddleware: Successfully left restricted chat", chat_id=event.chat.id)
                except TelegramAPIError as error:
                    await logger.aexception(
                        "SaveChatsMiddleware: Failed to leave restricted chat", chat_id=event.chat.id, error=str(error)
                    )
                if group := await ChatRepository.get_by_chat_id(event.chat.id):
                    await ChatRepository.delete_chat(group)
                return False

        joined_group = (
            event.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}
            and old_status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}
            and status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR}
        )
        if joined_group:
            await logger.ainfo(
                "SaveChatsMiddleware: Bot added to group, sending welcome message",
                chat_id=event.chat.id,
                old_status=old_status,
                status=status,
            )
            await cls._send_group_welcome_message(event)

        return status != ChatMemberStatus.MEMBER

    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        continue_ = True
        if not isinstance(event, Update):
            return await handler(event, data)

        await logger.adebug("SaveChatsMiddleware: Incoming update", update_id=event.update_id)
        if event.message:
            await self.handle_message(event.message, data)
        elif event.callback_query or event.inline_query or event.poll_answer:
            await self.save_from_user(data)
        elif event.chat_join_request:
            await self.save_chat_join_request(event.chat_join_request, data)
        elif event.my_chat_member:
            continue_ = await self.save_my_chat_member(event.my_chat_member)

        return await handler(event, data) if continue_ else None
