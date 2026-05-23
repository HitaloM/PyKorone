from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as _date
from enum import Enum
from typing import TYPE_CHECKING, cast

import orjson
from aiogram import flags
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

from korone.filters.admin_rights import UserRestricting
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.middlewares.chat_context import ChatContext
    from korone.modules.metadata import LoadedModule

VERSION = 6

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type ExportValue = JsonValue

EXPORTABLE_MODULES: list[LoadedModule] = []


def text_to_buffered_file(text: str, filename: str = "data.txt") -> BufferedInputFile:
    return BufferedInputFile(text.encode(), filename=filename)


def _make_serializable(obj: ExportValue | Enum | datetime | _date) -> ExportValue:
    if isinstance(obj, dict):
        return {str(k): _make_serializable(cast("ExportValue | Enum | datetime | _date", v)) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_make_serializable(cast("ExportValue | Enum | datetime | _date", v)) for v in obj]
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (datetime, _date)):
        return obj.isoformat()
    return obj


@flags.help(description=l_("Export your available data as a JSON file."))
class TriggerExport(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return Command("export"), UserRestricting(admin=True)

    @staticmethod
    async def get_data(chat: ChatContext) -> list[dict[str, ExportValue]]:
        exports: list[dict[str, ExportValue]] = []
        for module in EXPORTABLE_MODULES:
            if chat.type != ChatType.PRIVATE and module.export_private_only:
                continue

            if data := await module.export_data(chat.chat_id):
                exports.append(cast("dict[str, ExportValue]", data))

        return exports

    async def handle(self) -> None:
        await self.event.reply(_("Export is started, this may take a while."))

        data = self.get_initial_data(self.chat)
        modules_data = await self.get_data(self.chat)

        for module_data in modules_data:
            data.update(module_data)

        jfile = text_to_buffered_file(orjson.dumps(_make_serializable(data), option=orjson.OPT_INDENT_2).decode())
        text = _("Export is done.")
        await self.event.reply_document(jfile, caption=text)

    @staticmethod
    def get_initial_data(chat: ChatContext) -> dict[str, ExportValue]:
        return {
            "general": {
                "chat_name": chat.title,
                "chat_id": chat.chat_id,
                "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                "version": VERSION,
            },
            "chat_db": _make_serializable(cast("ExportValue | Enum | datetime | _date", chat.db_model.to_dict())),
        }
