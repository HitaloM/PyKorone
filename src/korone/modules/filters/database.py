# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M.

import time

import orjson

from korone.database.query import Query
from korone.database.table import Document
from korone.modules.filters.utils.types import Button, FilterFile, FilterModel, UserModel
from korone.utils.caching import cache
from korone.client import Korone


async def save_filter(
    client: Korone,
    chat_id: int,
    filter_names: tuple[str, ...],
    filter_text: str,
    content_type: str,
    creator_id: int,
    editor_id: int,
    file_id: str | None = None,
    buttons: list[list[Button]] | None = None,
) -> None:
    buttons = buttons or []
    filters_table = await client.db_connection.table("Filters")

    serialized_names = orjson.dumps(filter_names).decode()
    serialized_buttons = orjson.dumps([
        [button.model_dump() for button in row] for row in buttons
    ]).decode()
    current_timestamp = int(time.time())

    existing_filters = await filters_table.query(Query().chat_id == chat_id)

    existing_filter = await filters_table.query(
        (Query().chat_id == chat_id) & (Query().filter_names == serialized_names)
    )

    if existing_filter:
        existing_filter = existing_filter[0]
        created_date = existing_filter["created_date"]
        creator_id = existing_filter["creator_id"]

        await filters_table.update(
            Document(
                filter_text=filter_text,
                content_type=content_type,
                created_date=created_date,
                creator_id=creator_id,
                edited_date=current_timestamp,
                editor_id=editor_id,
                file_id=file_id,
                buttons=serialized_buttons,
            ),
            (Query().chat_id == chat_id) & (Query().filter_names == serialized_names),
        )
    else:
        await filters_table.insert(
            Document(
                chat_id=chat_id,
                filter_names=serialized_names,
                file_id=file_id,
                filter_text=filter_text,
                content_type=content_type,
                created_date=current_timestamp,
                creator_id=creator_id,
                edited_date=current_timestamp,
                editor_id=editor_id,
                buttons=serialized_buttons,
            )
        )

    for existing_filter in existing_filters:
        existing_filter_names = tuple(orjson.loads(existing_filter["filter_names"]))
        if set(existing_filter_names).intersection(set(filter_names)):
            updated_filter_names = tuple(
                name for name in existing_filter_names if name not in filter_names
            )
            if updated_filter_names:
                await filters_table.update(
                    Document(
                        filter_names=orjson.dumps(updated_filter_names).decode(),
                        edited_date=current_timestamp,
                        editor_id=editor_id,
                    ),
                    (Query().chat_id == chat_id)
                    & (Query().filter_names == orjson.dumps(existing_filter_names).decode()),
                )
            elif existing_filter_names != filter_names:
                await filters_table.delete(
                    (Query().chat_id == chat_id)
                    & (Query().filter_names == orjson.dumps(existing_filter_names).decode())
                )


async def list_filters(client: Korone, chat_id: int) -> list[FilterModel]:
    filters_table = await client.db_connection.table("Filters")
    filters = await filters_table.query(Query().chat_id == chat_id)
    return [deserialize_filter(filter) for filter in filters]


def deserialize_filter(filter: Document) -> FilterModel:
    return FilterModel(**{
        **filter,
        "filter_names": tuple(orjson.loads(filter["filter_names"])),
        "buttons": [
            [
                Button(**button) if isinstance(button, dict) else Button(**orjson.loads(button))
                for button in (
                    button_row if isinstance(button_row, list) else orjson.loads(button_row)
                )
            ]
            for button_row in (
                filter["buttons"]
                if isinstance(filter["buttons"], list)
                else orjson.loads(filter["buttons"])
            )
        ],
        "file": FilterFile(id=filter["file_id"], type=filter["content_type"])
        if filter["file_id"] and filter["content_type"]
        else None,
    })


async def delete_filter(client: Korone, chat_id: int, filter_names: tuple[str, ...]) -> None:
    filters_table = await client.db_connection.table("Filters")

    filters = await filters_table.query(Query().chat_id == chat_id)

    for filter in filters:
        existing_filter_names = tuple(orjson.loads(filter["filter_names"]))
        if updated_filter_names := tuple(
            name for name in existing_filter_names if name not in filter_names
        ):
            await filters_table.update(
                Document(
                    filter_names=orjson.dumps(updated_filter_names).decode(),
                    edited_date=int(time.time()),
                    editor_id=filter["editor_id"],
                ),
                (Query().chat_id == chat_id)
                & (Query().filter_names == orjson.dumps(existing_filter_names).decode()),
            )
        else:
            await filters_table.delete(
                (Query().chat_id == chat_id)
                & (Query().filter_names == orjson.dumps(existing_filter_names).decode())
            )


async def delete_all_filters(client: Korone, chat_id: int) -> bool:
    filters_table = await client.db_connection.table("Filters")

    existing_filters = await filters_table.query(Query().chat_id == chat_id)
    if not existing_filters:
        return False

    await filters_table.delete(Query().chat_id == chat_id)
    return True


async def get_filter_info(client: Korone, chat_id: int, filter_name: str) -> FilterModel | None:
    filters_table = await client.db_connection.table("Filters")
    users_table = await client.db_connection.table("Users")

    filters = await filters_table.query(Query().chat_id == chat_id)

    for filter in filters:
        if filter_name in (filter_names := tuple(orjson.loads(filter["filter_names"]))):
            creator = (await users_table.query(Query().id == filter["creator_id"]))[0]
            editor = (await users_table.query(Query().id == filter["editor_id"]))[0]

            return FilterModel(**{
                **filter,
                "filter_names": filter_names,
                "buttons": [
                    [
                        Button(**button)
                        if isinstance(button, dict)
                        else Button(**orjson.loads(button))
                        for button in (
                            button_row
                            if isinstance(button_row, list)
                            else orjson.loads(button_row)
                        )
                    ]
                    for button_row in (
                        filter["buttons"]
                        if isinstance(filter["buttons"], list)
                        else orjson.loads(filter["buttons"])
                    )
                ],
                "file": FilterFile(id=filter["file_id"], type=filter["content_type"])
                if filter["file_id"] and filter["content_type"]
                else None,
                "creator_id": UserModel(
                    id=creator["id"],
                    first_name=creator.get("first_name"),
                    last_name=creator.get("last_name"),
                    username=creator.get("username"),
                    language=creator.get("language", "en"),
                    registry_date=creator.get("registry_date"),
                )
                if creator
                else None,
                "editor_id": UserModel(
                    id=editor["id"],
                    first_name=editor.get("first_name"),
                    last_name=editor.get("last_name"),
                    username=editor.get("username"),
                    language=editor.get("language", "en"),
                    registry_date=editor.get("registry_date"),
                )
                if editor
                else None,
            })

    return None


async def update_filters_cache(client: Korone, chat_id: int) -> list[FilterModel]:
    await cache.delete(f"filters_cache:{chat_id}")
    filters = await list_filters(client, chat_id)
    serialized_filters = [filter.model_dump(by_alias=True) for filter in filters]
    await cache.set(f"filters_cache:{chat_id}", serialized_filters)
    return filters


async def get_filters_cache(client: Korone, chat_id: int) -> list[FilterModel]:
    if not (filters := await cache.get(f"filters_cache:{chat_id}")):
        filters = await update_filters_cache(client, chat_id)
    else:
        filters = [FilterModel(**filter) for filter in filters]
    return filters
