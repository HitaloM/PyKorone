# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M.

import json
import time
from collections import defaultdict

from korone import cache
from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document, Documents, Table
from korone.modules.filters.utils.types import Button, FilterFile, FilterModel, UserModel


async def save_filter(
    chat_id: int,
    filter_names: tuple[str, ...],
    filter_text: str,
    content_type: str,
    creator_id: int,
    editor_id: int,
    file_id: str | None = None,
    file_type: str | None = None,
    buttons: list[list[Button]] | None = None,
) -> None:
    buttons = buttons or []
    async with SQLite3Connection() as connection:
        filters_table = await connection.table("Filters")
        query = Query()

        serialized_names = json.dumps(filter_names)
        serialized_buttons = json.dumps([
            [button.model_dump() for button in row] for row in buttons
        ])
        current_timestamp = int(time.time())

        existing_filters = await filters_table.query(query.chat_id == chat_id)
        filters_to_remove, filters_to_update = classify_filters(existing_filters, filter_names)

        await remove_filters(filters_table, query, chat_id, filters_to_remove)
        await update_filters(
            filters_table,
            query,
            chat_id,
            filters_to_update,
            filter_names,
            editor_id,
            current_timestamp,
        )
        await insert_new_filter(
            filters_table,
            chat_id,
            serialized_names,
            filter_text,
            content_type,
            creator_id,
            editor_id,
            current_timestamp,
            file_id,
            file_type,
            serialized_buttons,
        )


def classify_filters(
    existing_filters: Documents, new_filter_names: tuple[str, ...]
) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    classified = defaultdict(list)
    new_filter_set = set(new_filter_names)

    for existing_filter in existing_filters:
        existing_filter_names = tuple(json.loads(existing_filter["filter_names"]))
        existing_filter_set = set(existing_filter_names)

        if existing_filter_set.issubset(new_filter_set):
            classified["remove"].append(existing_filter_names)
        elif new_filter_set.intersection(existing_filter_set):
            classified["update"].append(existing_filter_names)

    return classified["remove"], classified["update"]


async def remove_filters(
    filters_table: Table, query: Query, chat_id: int, filters_to_remove: list[tuple[str, ...]]
) -> None:
    for filter_names in filters_to_remove:
        await filters_table.delete(
            (query.chat_id == chat_id) & (query.filter_names == json.dumps(filter_names))
        )


async def update_filters(
    filters_table: Table,
    query: Query,
    chat_id: int,
    filters_to_update: list[tuple[str, ...]],
    new_filter_names: tuple[str, ...],
    editor_id: int,
    current_timestamp: int,
) -> None:
    for filter_names in filters_to_update:
        updated_filter_names = tuple(name for name in filter_names if name not in new_filter_names)
        if updated_filter_names:
            await filters_table.update(
                Document(
                    filter_names=json.dumps(updated_filter_names),
                    edited_date=current_timestamp,
                    editor_id=editor_id,
                ),
                (query.chat_id == chat_id) & (query.filter_names == json.dumps(filter_names)),
            )
        else:
            await filters_table.delete(
                (query.chat_id == chat_id) & (query.filter_names == json.dumps(filter_names))
            )


async def insert_new_filter(
    filters_table: Table,
    chat_id: int,
    serialized_names: str,
    filter_text: str,
    content_type: str,
    creator_id: int,
    editor_id: int,
    current_timestamp: int,
    file_id: str | None,
    file_type: str | None,
    serialized_buttons: str,
) -> None:
    await filters_table.insert(
        Document(
            chat_id=chat_id,
            filter_names=serialized_names,
            file_id=file_id,
            file_type=file_type,
            filter_text=filter_text,
            content_type=content_type,
            created_date=current_timestamp,
            creator_id=creator_id,
            edited_date=current_timestamp,
            editor_id=editor_id,
            buttons=serialized_buttons,
        )
    )


async def list_filters(chat_id: int) -> list[FilterModel]:
    async with SQLite3Connection() as connection:
        filters_table = await connection.table("Filters")
        query = Query()
        filters = await filters_table.query(query.chat_id == chat_id)
        return [deserialize_filter(filter) for filter in filters]


def deserialize_filter(filter: Document) -> FilterModel:
    return FilterModel(**{
        **filter,
        "filter_names": tuple(json.loads(filter["filter_names"])),
        "buttons": [
            [
                Button(**button) if isinstance(button, dict) else Button(**json.loads(button))
                for button in (
                    button_row if isinstance(button_row, list) else json.loads(button_row)
                )
            ]
            for button_row in (
                filter["buttons"]
                if isinstance(filter["buttons"], list)
                else json.loads(filter["buttons"])
            )
        ],
        "file": FilterFile(id=filter["file_id"], type=filter["content_type"])
        if filter["file_id"] and filter["content_type"]
        else None,
    })


async def delete_filter(chat_id: int, filter_names: tuple[str, ...]) -> None:
    async with SQLite3Connection() as connection:
        filters_table = await connection.table("Filters")
        query = Query()

        filters = await filters_table.query(query.chat_id == chat_id)

        for filter in filters:
            existing_filter_names = tuple(json.loads(filter["filter_names"]))
            updated_filter_names = tuple(
                name for name in existing_filter_names if name not in filter_names
            )
            if updated_filter_names:
                await filters_table.update(
                    Document(
                        filter_names=json.dumps(updated_filter_names),
                        edited_date=int(time.time()),
                        editor_id=filter["editor_id"],
                    ),
                    (query.chat_id == chat_id)
                    & (query.filter_names == json.dumps(existing_filter_names)),
                )
            else:
                await filters_table.delete(
                    (query.chat_id == chat_id)
                    & (query.filter_names == json.dumps(existing_filter_names))
                )


async def delete_all_filters(chat_id: int) -> None:
    async with SQLite3Connection() as connection:
        filters_table = await connection.table("Filters")
        query = Query()
        await filters_table.delete(query.chat_id == chat_id)


async def get_filter_info(chat_id: int, filter_name: str) -> FilterModel | None:
    async with SQLite3Connection() as connection:
        filters_table = await connection.table("Filters")
        users_table = await connection.table("Users")
        query = Query()

        filters = await filters_table.query(query.chat_id == chat_id)

        for filter in filters:
            if filter_name in (filter_names := tuple(json.loads(filter["filter_names"]))):
                creator = (await users_table.query(query.id == filter["creator_id"]))[0]
                editor = (await users_table.query(query.id == filter["editor_id"]))[0]

                return FilterModel(**{
                    **filter,
                    "filter_names": filter_names,
                    "buttons": [
                        [
                            Button(**button)
                            if isinstance(button, dict)
                            else Button(**json.loads(button))
                            for button in (
                                button_row
                                if isinstance(button_row, list)
                                else json.loads(button_row)
                            )
                        ]
                        for button_row in (
                            filter["buttons"]
                            if isinstance(filter["buttons"], list)
                            else json.loads(filter["buttons"])
                        )
                    ],
                    "file": FilterFile(id=filter["file_id"], type=filter["file_type"])
                    if filter["file_id"] and filter["file_type"]
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


async def update_filters_cache(chat_id: int) -> list[FilterModel]:
    await cache.delete(f"filters_cache:{chat_id}")
    filters = await list_filters(chat_id)
    serialized_filters = [filter.model_dump(by_alias=True) for filter in filters]
    await cache.set(f"filters_cache:{chat_id}", serialized_filters)
    return filters


async def get_filters_cache(chat_id: int) -> list[FilterModel]:
    if not (filters := await cache.get(f"filters_cache:{chat_id}")):
        filters = await update_filters_cache(chat_id)
    else:
        filters = [FilterModel(**filter) for filter in filters]
    return filters
