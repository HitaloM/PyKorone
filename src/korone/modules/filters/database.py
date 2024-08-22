# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import json
import time

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document, Documents, Table
from korone.modules.filters.utils.types import FilterModel


async def save_filter(
    chat_id: int,
    filter_names: tuple[str, ...],
    message_content: str,
    content_type: str,
    creator_id: int,
    editor_id: int,
    file_id: str | None = None,
) -> None:
    async with SQLite3Connection() as conn:
        table = await conn.table("Filters")
        query = Query()

        filter_text = json.dumps(filter_names)
        current_time = int(time.time())

        existing_filters = await table.query(query.chat_id == chat_id)
        filters_to_remove, filters_to_update = _classify_filters(existing_filters, filter_names)

        await _remove_filters(table, query, chat_id, filters_to_remove)
        await _update_filters(
            table, query, chat_id, filters_to_update, filter_names, editor_id, current_time
        )

        await table.insert(
            Document(
                chat_id=chat_id,
                filters=filter_text,
                file_id=file_id,
                message=message_content,
                content_type=content_type,
                created_date=current_time,
                creator_id=creator_id,
                edited_date=current_time,
                editor_id=editor_id,
            )
        )


def _classify_filters(
    existing_filters: Documents, filter_names: tuple[str, ...]
) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    filters_to_remove: list[tuple[str, ...]] = []
    filters_to_update: list[tuple[str, ...]] = []
    for existing_filter in existing_filters:
        existing_filter_name = tuple(json.loads(existing_filter["filters"]))
        if set(existing_filter_name).issubset(set(filter_names)):
            filters_to_remove.append(existing_filter_name)
        elif set(filter_names).intersection(set(existing_filter_name)):
            filters_to_update.append(existing_filter_name)
    return filters_to_remove, filters_to_update


async def _remove_filters(
    table: Table, query: Query, chat_id: int, filters_to_remove: list[tuple[str, ...]]
) -> None:
    for filter_to_remove in filters_to_remove:
        await table.delete(
            (query.chat_id == chat_id) & (query.filters == json.dumps(filter_to_remove))
        )


async def _update_filters(
    table: Table,
    query: Query,
    chat_id: int,
    filters_to_update: list[tuple[str, ...]],
    filter_names: tuple[str, ...],
    editor_id: int,
    current_time: int,
) -> None:
    for filter_to_update in filters_to_update:
        updated_filter_name = tuple(item for item in filter_to_update if item not in filter_names)
        if updated_filter_name:
            updated_filter_text = json.dumps(updated_filter_name)
            await table.update(
                Document(
                    filters=updated_filter_text,
                    edited_date=current_time,
                    editor_id=editor_id,
                ),
                (query.chat_id == chat_id) & (query.filters == json.dumps(filter_to_update)),
            )
        else:
            await table.delete(
                (query.chat_id == chat_id) & (query.filters == json.dumps(filter_to_update))
            )


async def list_filters(chat_id: int) -> list[FilterModel]:
    async with SQLite3Connection() as conn:
        table = await conn.table("Filters")
        query = Query()
        filters = await table.query(query.chat_id == chat_id)
        return [
            FilterModel(**{**filter, "filters": tuple(json.loads(filter["filters"]))})
            for filter in filters
        ]
