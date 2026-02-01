from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags
from stfu_tg import Code, Doc, KeyValue, Section

from korone.db.session import get_sqlite_runtime_info, get_sqlite_stats
from korone.filters.cmd import CMDFilter
from korone.filters.user_status import IsOP
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Show SQLite runtime info (WAL, synchronous, timeouts)."))
class SQLiteInfoHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("sqlite", "dbinfo")), IsOP(is_op=True))

    async def handle(self) -> None:
        runtime = await get_sqlite_runtime_info()
        size = await get_sqlite_stats()

        if not runtime:
            await self.event.reply("SQLite is not the current database backend")
            return

        sec = Section(title="SQLite")
        sec += KeyValue("journal_mode", Code(str(runtime.get("journal_mode", ""))))
        sec += KeyValue("synchronous", Code(str(runtime.get("synchronous", ""))))
        sec += KeyValue("foreign_keys", Code(int(runtime.get("foreign_keys", 0))))
        sec += KeyValue("busy_timeout", Code(f"{int(runtime.get('busy_timeout_ms', 0))} ms"))
        sec += KeyValue("wal_autocheckpoint", Code(int(runtime.get("wal_autocheckpoint", 0))))
        sec += KeyValue("cache_size", Code(int(runtime.get("cache_size", 0))))

        sec += KeyValue("page_count", Code(size.get("page_count", 0)))
        sec += KeyValue("page_size", Code(size.get("page_size", 0)))
        sec += KeyValue("db_size", Code(size.get("db_size", 0)))

        await self.event.reply(str(Doc(sec)))
