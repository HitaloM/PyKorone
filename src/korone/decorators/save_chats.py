# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram.enums import ChatType
from hydrogram.types import Chat, Message, User

from korone.config import ConfigManager
from korone.decorators.database import DatabaseManager


class ChatManager:
    """
    Save chats and users to the database.

    This class handles all operations related to the database for the Factory decorator.
    It provides methods to save chats and users to the database.

    Attributes
    ----------
    database_manager : DatabaseManager
        The database manager to handle database operations.
    """

    __slots__ = ("database_manager",)

    def __init__(self) -> None:
        self.database_manager = DatabaseManager()

    async def _update_user_or_chat(
        self, user_or_chat: User | Chat, language: str | None = None
    ) -> None:
        """
        Update or create a user or chat in the database.

        Parameters
        ----------
        user_or_chat : User | Chat
            The user or chat object to update or create.
        language : str, optional
            The language code of the user, if applicable.
        """
        await self.database_manager.update_or_create(user_or_chat, language)

    async def _handle_private_and_group_message(self, message: Message) -> None:
        """
        Handle private and group messages.

        This method handles private and group messages. If the message is from a private chat,
        it updates or creates the user object. If the message is from a group or supergroup,
        it updates or creates the chat object.

        Parameters
        ----------
        message : Message
            The message object.
        """
        if message.from_user and not message.from_user.is_bot:
            await self._update_user_or_chat(message.from_user, message.from_user.language_code)

        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await self._update_user_or_chat(message.chat)

    async def _handle_message_update(self, message: Message) -> list[Chat | User]:
        """
        Handle message updates.

        This method handles message updates. If the message is a reply to a message, it
        updates or creates the user object of the replied message. If the message is a
        forwarded message, it updates or creates the chat object of the forwarded message.

        Parameters
        ----------
        message : Message
            The message object.

        Returns
        -------
        list[Chat | User]
            The list of chats to update.
        """
        chats_to_update = []

        if reply_message := message.reply_to_message:
            chats_to_update.extend(await self.handle_replied_message(reply_message))

        if message.forward_from or (
            message.forward_from_chat and message.forward_from_chat.id != message.chat.id
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
        """
        if message.new_chat_members:
            for member in message.new_chat_members:
                if not member.is_bot:
                    await self._update_user_or_chat(member, member.language_code)

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
        await self._handle_private_and_group_message(message)

        chats_to_update = await self._handle_message_update(message)
        await self._handle_member_updates(message)
        await self._chats_update(chats_to_update)

    async def _chats_update(self, chats: list[Chat | User]) -> None:
        """
        Update chats.

        This method updates the chats based on the list of chats.

        Parameters
        ----------
        chats : list[Chat | User]
            The list of chats to update.
        """
        if chats:
            for chat in chats:
                language = chat.language_code if isinstance(chat, User) else None
                await self._update_user_or_chat(chat, language)

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
            await self._update_user_or_chat(user, user.language_code)

    @staticmethod
    async def handle_replied_message(message: Message) -> list[Chat | User]:
        """
        Handle replied message.

        This method handles the replied message. It updates or creates the user object of the
        replied message. If the replied message is a forwarded message, it updates or creates
        the chat object of the forwarded message.

        Parameters
        ----------
        message : Message
            The message object.

        Returns
        -------
        list[Chat | User]
            The list of chats to update.
        """
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
