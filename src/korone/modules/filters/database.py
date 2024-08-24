# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import json
import time

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document, Documents, Table
from korone.modules.filters.utils import FilterModel


async def save_filter(
    chat_id: int,
    filter_names: tuple[str, ...],
    filter_text: str,
    content_type: str,
    creator_id: int,
    editor_id: int,
    file_id: str | None = None,
) -> None:
    async with SQLite3Connection() as connection:
        filters_table = await connection.table("Filters")
        query = Query()

        serialized_names = json.dumps(filter_names)
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
        )


def classify_filters(
    existing_filters: Documents, new_filter_names: tuple[str, ...]
) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    filters_to_remove: list[tuple[str, ...]] = []
    filters_to_update: list[tuple[str, ...]] = []
    for existing_filter in existing_filters:
        existing_filter_names = tuple(json.loads(existing_filter["filter_names"]))
        if set(existing_filter_names).issubset(set(new_filter_names)):
            filters_to_remove.append(existing_filter_names)
        elif set(new_filter_names).intersection(set(existing_filter_names)):
            filters_to_update.append(existing_filter_names)
    return filters_to_remove, filters_to_update


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
            updated_filter_text = json.dumps(updated_filter_names)
            await filters_table.update(
                Document(
                    filter_names=updated_filter_text,
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
) -> None:
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
        )
    )


async def list_filters(chat_id: int) -> list[FilterModel]:
    async with SQLite3Connection() as connection:
        filters_table = await connection.table("Filters")
        query = Query()
        filters = await filters_table.query(query.chat_id == chat_id)
        return [
            FilterModel(**{**filter, "filter_names": tuple(json.loads(filter["filter_names"]))})
            for filter in filters
        ]


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
                updated_filter_text = json.dumps(updated_filter_names)
                await filters_table.update(
                    Document(
                        filter_names=updated_filter_text,
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
