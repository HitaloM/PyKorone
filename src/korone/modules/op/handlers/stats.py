from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command
from pydantic import ByteSize

from korone import aredis
from korone.db.session import get_postgres_stats
from korone.filters.user_status import IsOP
from korone.modules import LOADED_MODULES
from korone.utils.formatting import Code, Doc, KeyValue, Section, Template
from korone.utils.handlers import KoroneMessageHandler

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


async def get_system_stats() -> Doc:
    doc = Doc()

    technical_section = Section(title="Technical info")

    local_db = await get_postgres_stats()
    technical_section += KeyValue(
        "Database size",
        Template("{db_size}", db_size=Code(ByteSize(local_db["db_size"]).human_readable(decimal=False))),
    )

    technical_section += KeyValue("Redis keys", Code(await aredis.dbsize()))
    technical_section += KeyValue("Modules", Template("{modules} loaded", modules=Code(len(LOADED_MODULES))))

    doc += technical_section
    return doc


@flags.help(description="Show bot and module statistics.")
class StatsHandler(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("stats"), IsOP(is_op=True))

    async def handle(self) -> None:
        sec = Doc()

        for module in LOADED_MODULES.values():
            if res := await module.collect_stats():
                sec += res

        await self.event.reply(str(sec))
