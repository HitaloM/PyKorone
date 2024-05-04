# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import pickle
from collections.abc import Callable
from functools import wraps

from babel import Locale
from babel.core import UnknownLocaleError
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, Chat, Message, User

from korone import i18n, redis
from korone.config import ConfigManager
from korone.decorators.database import DatabaseManager


class ChatManager:
    """
    Save chats and users to the database.

    This class is used to handle all operations related to the database on Factory decorator.
    It provides methods to save chats and users to the database.

    Attributes
    ----------
    database_manager : DatabaseManager
        The database manager to handle database operations.
    """

    __slots__ = ("database_manager",)

    def __init__(self) -> None:
        self.database_manager = DatabaseManager()

    async def get_locale(self, chat: User | Chat) -> str:
        """
        Get the locale based on the user and message.

        This method returns the locale based on the user and message. If the user or chat
        is not a bot, it retrieves the database object and gets the locale from it. If the
        database object is empty, it returns the default locale. If the locale is not available,
        it returns the default locale.

        Parameters
        ----------
        chat : User | Chat
            The user or chat object.

        Returns
        -------
        str
            The locale based on the user or chat.

        Raises
        ------
        UnknownLocaleError
            If the locale identifier is invalid.
        """
        cache_key = f"locale_cache:{chat.id}"
        cached_data = await redis.get(cache_key)
        if cached_data:
            return pickle.loads(cached_data)

        db_obj = None
        if (isinstance(chat, User) and not chat.is_bot) or (
            isinstance(chat, Chat) and chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}
        ):
            db_obj = await self.database_manager.get(chat)

        try:
            if db_obj and "_" not in db_obj[0]["language"]:
                locale = (
                    Locale.parse(db_obj[0]["language"], sep="-") if db_obj else i18n.default_locale
                )
            elif db_obj:
                locale = Locale.parse(db_obj[0]["language"])

            if db_obj and isinstance(locale, Locale):
                locale = f"{locale.language}_{locale.territory}"
            if db_obj and locale not in i18n.available_locales:
                msg = "Invalid locale identifier"
                raise UnknownLocaleError(msg)

        except UnknownLocaleError:
            locale = i18n.default_locale

        pickled_data = pickle.dumps(locale)
        ttl = 86400  # 24 hours
        await redis.set(cache_key, pickled_data, ttl)

        return str(locale)

    async def _handle_private_and_group_message(self, chat_id: int, message: Message) -> None:
        """
        Handle private and group messages.

        This method handles private and group messages. If the message is from a private chat,
        it updates or creates the user object. If the message is from a group or supergroup,
        it updates or creates the chat object.

        Parameters
        ----------
        chat_id : int
            The chat ID.
        message : Message
            The message object.

        Notes
        -----
        This method is a private method and should not be called outside of the class.
        """
        if message.from_user and not message.from_user.is_bot:
            await self.database_manager.update_or_create(
                message.from_user, message.from_user.language_code
            )
        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await self.database_manager.update_or_create(message.chat)

    async def _handle_message_update(self, chat_id: int, message: Message) -> list[Chat | User]:
        """
        Handle message updates.

        This method handles message updates. If the message is a reply to a message, it
        updates or creates the user object of the replied message. If the message is a
        forwarded message, it updates or creates the chat object of the forwarded message.

        Parameters
        ----------
        chat_id : int
            The chat ID.
        message : Message
            The message object.

        Returns
        -------
        list[Chat | User]
            The list of chats to update.

        Notes
        -----
        This method is a private method and should not be called outside of the class.
        """
        chats_to_update = []

        if reply_message := message.reply_to_message:
            chats_to_update.extend(await self.handle_replied_message(chat_id, reply_message))
        if message.forward_from or (
            message.forward_from_chat and message.forward_from_chat.id != chat_id
        ):
            chats_to_update.append(message.forward_from_chat or message.forward_from)

        return chats_to_update

    async def _handle_member_updates(self, message: Message) -> None:
        """
        Handle member updates.

        This method handles member updates. If the message has new chat members, it updates
        or creates the user object of the new chat members.

        Parameters
        ----------
        message : Message
            The message object.

        Notes
        -----
        This method is a private method and should not be called outside of the class.
        """
        if message.new_chat_members:
            for member in message.new_chat_members:
                if not member.is_bot:
                    await self.database_manager.update_or_create(member, member.language_code)

    async def _chats_update(self, chats: list[Chat | User]) -> None:
        """
        Update chats.

        This method updates the chats based on the list of chats.

        Parameters
        ----------
        chats : list[Chat | User]
            The list of chats to update.
        """
        if not chats:
            return
        for chat in chats:
            language = chat.language_code if isinstance(chat, User) else None
            await self.database_manager.update_or_create(chat, language)

    def handle_chat(self, func: Callable) -> Callable:
        """
        Handle chat.

        This method handles the chat based on the update. If the update is a message, it
        handles the message. If the update is a callback query, it saves the user object.

        Parameters
        ----------
        func : Callable
            The function to be wrapped.

        Returns
        -------
        Callable
            The wrapper function.
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            update: Message | CallbackQuery

            try:
                update = args[2]
            except IndexError:
                update = args[1]

            is_callback = isinstance(update, CallbackQuery)
            message = update.message if is_callback else update
            user: User = update.from_user if is_callback else message.from_user

            if is_callback:
                await self.save_from_user(user)
            else:
                await self.handle_message(message)

            locale = i18n.default_locale
            if message.chat.type == ChatType.PRIVATE and user and not user.is_bot:
                locale = await self.get_locale(user)
            elif message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
                locale = await self.get_locale(message.chat)

            with i18n.context(), i18n.use_locale(locale):
                return await func(*args, **kwargs)

        return wrapper

    async def save_from_user(self, user: User) -> None:
        """
        Save the user object to the database.

        This method saves the user object to the database.

        Parameters
        ----------
        user : User
            The user object.
        """
        if user and not user.is_bot:
            await self.database_manager.update_or_create(user, user.language_code)

    async def handle_message(self, message: Message) -> None:
        """
        Handle the message.

        This method handles the message. It updates or creates the user object if the message
        is from a private chat. It updates or creates the chat object if the message is from
        a group or supergroup. It also handles message updates and member updates.

        Parameters
        ----------
        message : Message
            The message object.
        """
        chat = message.chat

        await self._handle_private_and_group_message(chat.id, message)

        chats_to_update = await self._handle_message_update(chat.id, message)

        if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await self._handle_member_updates(message)

        await self._chats_update(chats_to_update)

    @staticmethod
    async def handle_replied_message(chat_id: int, message: Message) -> list[Chat | User]:
        """
        Handle replied message.

        This method handles the replied message. It updates or creates the user object of the
        replied message. If the replied message is a forwarded message, it updates or creates
        the chat object of the forwarded message.

        Parameters
        ----------
        chat_id : int
            The chat ID.
        message : Message
            The message object.

        Returns
        -------
        list[Chat | User]
            The list of chats to update.
        """
        if message.sender_chat and message.sender_chat.id == chat_id:
            return []

        if message.forum_topic_created:
            return []

        chats_to_update = []

        bot_token = ConfigManager.get("hydrogram", "BOT_TOKEN")
        bot_id = bot_token.split(":", 1)[0]

        replied_message_user = message.sender_chat or message.from_user
        if (
            replied_message_user
            and replied_message_user.id != bot_id
            and (isinstance(replied_message_user, Chat) or not replied_message_user.is_bot)
        ):
            chats_to_update.append(replied_message_user)

        reply_to_forwarded = message.forward_from_chat or message.forward_from
        if (
            reply_to_forwarded
            and reply_to_forwarded.id != bot_id
            and (isinstance(reply_to_forwarded, Chat) or not reply_to_forwarded.is_bot)
        ):
            chats_to_update.append(reply_to_forwarded)

        return chats_to_update
