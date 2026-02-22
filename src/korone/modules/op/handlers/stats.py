from __future__ import annotations

import math
from types import ModuleType
from typing import TYPE_CHECKING

from aiogram import flags
from stfu_tg import Code, Doc, KeyValue, Section, Template

from korone import aredis
from korone.db.session import get_postgres_stats
from korone.filters.cmd import CMDFilter
from korone.filters.user_status import IsOP
from korone.modules import LOADED_MODULES
from korone.utils.handlers import KoroneMessageHandler

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = math.floor(math.log(size_bytes, 1024))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


async def get_system_stats() -> Doc:
    doc = Doc()

    technical_section = Section(title="Technical info")

    local_db = await get_postgres_stats()
    technical_section += KeyValue(
        "Database size", Template("{db_size}", db_size=Code(convert_size(local_db["db_size"])))
    )

    technical_section += KeyValue("Redis keys", Code(await aredis.dbsize()))
    technical_section += KeyValue("Modules", Template("{modules} loaded", modules=Code(len(LOADED_MODULES))))

    doc += technical_section
    return doc


@flags.help(description="Show bot statistics.")
class StatsHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("stats",)), IsOP(is_op=True))

    async def handle(self) -> None:
        sec = Doc()

        all_modules: list[ModuleType | str] = list(LOADED_MODULES.values())
        all_modules.extend(LOADED_MODULES)

        for module in all_modules:
            if not isinstance(module, ModuleType):
                continue
            if hasattr(module, "__stats__"):
                res = module.__stats__()
                if hasattr(res, "__await__"):
                    res = await res
                sec += res

        await self.event.reply(str(sec))
