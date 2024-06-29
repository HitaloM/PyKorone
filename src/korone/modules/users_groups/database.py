# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import time

from hydrogram.types import Chat, User

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document, Documents


async def get_user_by_id(user_id: int) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Users")
        query = Query()
        return await table.query(query.id == user_id)


async def get_user_by_username(username: str) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Users")
        query = Query()
        return await table.query(query.username == username.lower())


async def save_user(user: User) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Users")
        query = Query()
        existing_user = await table.query(query.id == user.id)
        if not existing_user:
            new_user = Document(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                registry_date=int(time.time()),
            )
            await table.insert(new_user)
            return Documents([new_user])
        return existing_user


async def get_chat_by_id(chat_id: int) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Groups")
        query = Query()
        return await table.query(query.id == chat_id)


async def get_chat_by_username(username: str) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Groups")
        query = Query()
        return await table.query(query.username == username.lower())


async def save_chat(chat: Chat) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Groups")
        query = Query()
        existing_chat = await table.query(query.id == chat.id)
        if not existing_chat:
            new_chat = Document(
                id=chat.id,
                title=chat.title,
                username=chat.username,
                type=chat.type.name.lower(),
                registry_date=int(time.time()),
            )
            await table.insert(new_chat)
            return Documents([new_chat])
        return existing_chat
