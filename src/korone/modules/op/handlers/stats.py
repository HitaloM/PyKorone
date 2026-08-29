from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command
from pydantic import ByteSize

from korone import aredis
from korone.db.session import get_postgres_stats
from korone.filters.user_status import IsOP
from korone.modules import LOADED_MODULES
from korone.ui import Code, UIExpression, column, field, section, template
from korone.utils.handlers import KoroneMessageHandler

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


async def get_system_stats() -> UIExpression:
    local_db = await get_postgres_stats()
    return section(
        "Technical info",
        field(
            "Database size",
            template("{db_size}", db_size=Code(ByteSize(local_db["db_size"]).human_readable(decimal=False))),
        ),
        field("Redis keys", Code(await aredis.dbsize())),
        field("Modules", template("{modules} loaded", modules=Code(len(LOADED_MODULES)))),
    )


@flags.help(description="Show bot and module statistics.")
class StatsHandler(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("stats"), IsOP(is_op=True))

    async def handle(self) -> None:
        sections = [res for module in LOADED_MODULES.values() if (res := await module.collect_stats())]

        await self.answer(column(*sections))
