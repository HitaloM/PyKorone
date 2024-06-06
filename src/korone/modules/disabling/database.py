# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.sqlite import sqlite_pool
from korone.database.table import Document
from korone.modules import COMMANDS


async def set_command_state(chat_id: int, command: str, *, state: bool) -> None:
    async with sqlite_pool as conn:
        if command not in COMMANDS:
            msg = f"Command '{command}' has not been registered!"
            raise KeyError(msg)

        if "parent" in COMMANDS[command]:
            command = COMMANDS[command]["parent"]

        COMMANDS[command]["chat"][chat_id] = state

        table = await conn.table("Commands")
        query = Query()
        query = (query.chat_id == chat_id) & (query.command == command)
        if not await table.query(query):
            await table.insert(Document(chat_id=chat_id, command=command, state=state))
            return

        await table.update(Document(state=state), query)


async def disabled_commands(chat_id: int) -> list[str]:
    async with sqlite_pool as conn:
        table = await conn.table("Commands")
        query = Query()
        query = (query.chat_id == chat_id) & (query.state == 0)
        result = await table.query(query)
        return [doc["command"] for doc in result]
