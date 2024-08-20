# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import time
from enum import Enum

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document
from korone.modules.filters.utils.types import FilterModel


class FilterStatus(Enum):
    SAVED = "saved"
    UPDATED = "updated"


async def save_filter(
    chat_id: int,
    filter_text: str,
    message_content: str,
    content_type: str,
    creator_id: int,
    editor_id: int,
    file_id: str | None = None,
) -> FilterStatus:
    async with SQLite3Connection() as conn:
        table = await conn.table("Filters")
        query = Query()

        existing_filter = await table.query(
            (query.chat_id == chat_id) & (query.filter == filter_text)
        )

        if not existing_filter:
            await table.insert(
                Document(
                    chat_id=chat_id,
                    filter=filter_text,
                    file_id=file_id,
                    message=message_content,
                    content_type=content_type,
                    created_date=int(time.time()),
                    creator_id=creator_id,
                    edited_date=int(time.time()),
                    editor_id=editor_id,
                )
            )
            return FilterStatus.SAVED
        await table.update(
            Document(
                file_id=file_id or "",
                message=message_content,
                content_type=content_type,
                edited_date=int(time.time()),
                editor_id=editor_id,
            ),
            (query.chat_id == chat_id) & (query.filter == filter_text),
        )
        return FilterStatus.UPDATED


async def list_filters(chat_id: int) -> list[FilterModel]:
    async with SQLite3Connection() as conn:
        table = await conn.table("Filters")
        query = Query()
        filters = await table.query(query.chat_id == chat_id)
        return [FilterModel(**filter) for filter in filters]
