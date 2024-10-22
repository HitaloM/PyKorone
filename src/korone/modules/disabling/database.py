# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.table import Document
from korone.modules.core import COMMANDS
from korone.client import Korone


async def set_command_state(client: Korone, chat_id: int, command_name: str, *, state: bool) -> None:
    if command_name not in COMMANDS:
        msg = f"Command '{command_name}' has not been registered!"
        raise KeyError(msg)

    if "parent" in COMMANDS[command_name]:
        command_name = COMMANDS[command_name]["parent"]

    COMMANDS[command_name]["chat"][chat_id] = state

    table = await client.db_connection.table("Commands")
    query = (Query().chat_id == chat_id) & (Query().command == command_name)

    if not await table.query(query):
        await table.insert(Document(chat_id=chat_id, command=command_name, state=state))
        return

    await table.update(Document(state=state), query)


async def get_disabled_commands(client: Korone, chat_id: int) -> list[str]:
    table = await client.db_connection.table("Commands")
    query = (Query().chat_id == chat_id) & (Query().state == 0)

    result = await table.query(query)
    return [doc["command"] for doc in result]
