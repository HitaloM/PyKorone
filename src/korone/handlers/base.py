# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import inspect
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Final

from anyio import create_task_group
from babel import Locale, UnknownLocaleError
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, Chat, Message, Update, User

from korone.config import ConfigManager
from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document, Documents, Table
from korone.utils.caching import cache
from korone.utils.i18n import i18n

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.filters import Filter

BOT_ID: Final[int] = ConfigManager.get("hydrogram", "BOT_TOKEN").split(":", 1)[0]

type UpdateType = Update | Message | CallbackQuery
type ChatEntity = User | Chat


@dataclass(slots=True, frozen=False)
class BaseHandler:
    callback: Callable[..., Any]
    filters: Filter | None = None
    _background_tasks: set = field(default_factory=set, init=False, repr=False)

    @staticmethod
    async def _extract_message_and_user(update: UpdateType) -> tuple[Message | None, User | None]:
        if isinstance(update, CallbackQuery):
            return update.message, update.from_user
        if isinstance(update, Message):
            return update, update.from_user
        return None, None

    async def _fetch_locale(self, update: UpdateType) -> str:
        message, user = await self._extract_message_and_user(update)
        if not message or not user:
            return i18n.default_locale

        chat = message.chat
        if not chat:
            return i18n.default_locale

        if user and chat.type == ChatType.PRIVATE:
            return await self._fetch_locale_from_db(user)
        if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            return await self._fetch_locale_from_db(chat)
        return i18n.default_locale

    @cache(ttl=timedelta(days=1), key="fetch_locale:{chat.id}")
    async def _fetch_locale_from_db(self, chat: ChatEntity) -> str:
        if not self._is_valid_chat(chat):
            return i18n.default_locale

        db_obj = await self._get_document(chat)
        if not db_obj:
            return i18n.default_locale

        try:
            language = db_obj[0]["language"]
            sep = "-" if "_" not in language else "_"
            locale_obj = Locale.parse(language, sep=sep)
            locale = f"{locale_obj.language}_{locale_obj.territory}"
            if locale not in i18n.available_locales:
                msg = "Invalid locale identifier"
                raise UnknownLocaleError(msg)
        except UnknownLocaleError:
            locale = i18n.default_locale

        return str(locale)

    @staticmethod
    def _is_valid_chat(chat: ChatEntity) -> bool:
        if isinstance(chat, User):
            return not chat.is_bot
        if isinstance(chat, Chat):
            return chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}
        return False

    async def _process_update(self, client: Client, update: UpdateType) -> Callable | None:
        message, user = await self._extract_message_and_user(update)
        if not message:
            return None

        if isinstance(update, CallbackQuery) and user:
            await self._store_user_or_chat(user)
        else:
            await self._process_message(message)

        if user and not user.is_bot and message:
            return await self.callback(client, update)
        return None

    async def _validate(self, client: Client, update: UpdateType) -> bool:
        message, _ = await self._extract_message_and_user(update)
        if not message or not callable(self.filters):
            return False

        if inspect.iscoroutinefunction(self.filters.__call__):
            result = await self.filters(client, update)
            return bool(result)

        # Use executor for non-coroutine filters
        result = await client.loop.run_in_executor(client.executor, self.filters, client, update)
        if inspect.iscoroutine(result):
            result = await result

        return bool(result)

    async def _get_document(self, chat: ChatEntity) -> Documents | None:
        table_name = self._determine_table(chat)
        if not table_name:
            return None

        async with SQLite3Connection() as conn:
            table = await conn.table(table_name)
            return await table.query(Query().id == chat.id)

    @staticmethod
    def _determine_table(chat: ChatEntity) -> str | None:
        if isinstance(chat, User) or (isinstance(chat, Chat) and chat.type == ChatType.PRIVATE):
            return "Users"
        if isinstance(chat, Chat) and chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            return "Groups"
        return None

    @staticmethod
    async def _do_chat_migration(old_id: int, new_id: int) -> bool:
        async with SQLite3Connection() as conn:
            table = await conn.table("Groups")
            obj = await table.query(Query().id == old_id)

            if not obj:
                return False

            doc = obj[0]
            doc["id"] = new_id
            await table.update(doc, Query().id == old_id)
            return True

    async def _store_user_or_chat(
        self, user_or_chat: ChatEntity, language: str | None = None
    ) -> None:
        table_name = self._determine_table(user_or_chat)
        if not table_name:
            return

        async with SQLite3Connection() as conn:
            language = language or i18n.default_locale
            table = await conn.table(table_name)
            obj = await table.query(Query().id == user_or_chat.id)

            if obj:
                await self._update_document(user_or_chat, language, table, obj)
            else:
                await self._insert_document(user_or_chat, language, table)

    async def _update_document(
        self, chat: ChatEntity, language: str, table: Table, obj: Documents
    ) -> Documents:
        doc = self._create_document(chat, language)
        doc["registry_date"] = obj[0]["registry_date"]
        doc["language"] = obj[0]["language"]

        await table.update(doc, Query().id == chat.id)
        return Documents([doc])

    async def _insert_document(self, chat: ChatEntity, language: str, table: Table) -> Documents:
        doc = self._create_document(chat, language)
        await table.insert(doc)
        return Documents([doc])

    @staticmethod
    def _create_document(chat: ChatEntity, language: str) -> Document:
        username = (getattr(chat, "username", "") or "").lower()
        title = getattr(chat, "title", None)
        first_name = getattr(chat, "first_name", None)

        chat_type = None
        if isinstance(chat, Chat) and chat.type:
            chat_type = getattr(chat.type, "name", "").lower()

        last_name = getattr(chat, "last_name", "") if isinstance(chat, User) else None

        return Document(
            id=chat.id,
            title=title,
            first_name=first_name,
            last_name=last_name,
            username=username,
            type=chat_type,
            language=language,
            registry_date=int(time.time()),
        )

    async def _process_message(self, message: Message) -> None:
        if await self._process_migration(message):
            return

        await self._process_private_and_group_messages(message)

        if not message.chat or message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
            return

        chats_to_update = self._extract_chats_to_update(message)
        await self._update_chats(chats_to_update)

        await self._process_member_updates(message)

    async def _process_migration(self, message: Message) -> bool:
        if message.migrate_from_chat_id:
            new_id = message.chat.id if message.chat else 0
            return await self._do_chat_migration(message.migrate_from_chat_id, new_id)
        return bool(message.migrate_to_chat_id)

    async def _process_private_and_group_messages(self, message: Message) -> None:
        if message.from_user and not message.from_user.is_bot:
            await self._store_user_or_chat(message.from_user, message.from_user.language_code)

        if message.chat and message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await self._store_user_or_chat(message.chat)

    def _extract_chats_to_update(self, message: Message) -> list[ChatEntity]:
        chats_to_update = []

        # Process reply messages
        if reply_message := message.reply_to_message:
            chats_to_update.extend(self._extract_replied_message_chats(reply_message))

        # Process forwarded content
        forward_from_chat = message.forward_from_chat
        forward_from = message.forward_from

        if forward_from_chat and (not message.chat or forward_from_chat.id != message.chat.id):
            chats_to_update.append(forward_from_chat)

        if forward_from:
            chats_to_update.append(forward_from)

        return chats_to_update

    async def _process_member_updates(self, message: Message) -> None:
        if not message.new_chat_members:
            return

        async with create_task_group() as tg:
            for member in message.new_chat_members:
                if member.is_bot:
                    continue
                tg.start_soon(self._store_user_or_chat, member, member.language_code)

    async def _update_chats(self, chats: Sequence[ChatEntity]) -> None:
        if not chats:
            return

        async with create_task_group() as tg:
            for chat in chats:
                language_code = chat.language_code if isinstance(chat, User) else None
                tg.start_soon(self._store_user_or_chat, chat, language_code)

    @staticmethod
    def _extract_replied_message_chats(message: Message) -> list[ChatEntity]:
        chats_to_update = []

        # Process sender of replied message
        replied_message_user = message.sender_chat or message.from_user
        if (
            replied_message_user
            and replied_message_user.id != BOT_ID
            and (isinstance(replied_message_user, Chat) or not replied_message_user.is_bot)
        ):
            chats_to_update.append(replied_message_user)

        # Process forwarded content in replies
        reply_to_forwarded = message.forward_from_chat or message.forward_from
        if (
            reply_to_forwarded
            and reply_to_forwarded.id != BOT_ID
            and (isinstance(reply_to_forwarded, Chat) or not reply_to_forwarded.is_bot)
        ):
            chats_to_update.append(reply_to_forwarded)

        return chats_to_update

    async def _check_and_handle(self, client: Client, update: UpdateType) -> None:
        locale = await self._fetch_locale(update)
        with i18n.context(), i18n.use_locale(locale):
            if await self._validate(client, update):
                await self._process_update(client, update)
