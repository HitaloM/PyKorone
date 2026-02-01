from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as _date
from enum import Enum
from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.types import BufferedInputFile
from ujson import dumps

from korone.filters.cmd import CMDFilter
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from types import ModuleType

    from aiogram.dispatcher.event.handler import CallbackType

    from korone.middlewares.chat_context import ChatContext

VERSION = 6

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type ExportValue = JsonValue

EXPORTABLE_MODULES: list[ModuleType] = []


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


@flags.help(description=l_("Exports your data to a JSON file"))
class TriggerExport(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("export"),)

    @staticmethod
    async def get_data(chat_id: int) -> list[dict[str, ExportValue]]:
        return list(
            filter(
                None,
                [await module.__export__(chat_id) for module in EXPORTABLE_MODULES if hasattr(module, "__export__")],
            )
        )

    async def handle(self) -> None:
        await self.event.reply(_("Export is started, this may take a while."))

        data = self.get_initial_data(self.chat)
        modules_data = await self.get_data(self.chat.chat_id)

        for module_data in modules_data:
            data.update(module_data)

        jfile = text_to_buffered_file(dumps(_make_serializable(data), indent=2))
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
