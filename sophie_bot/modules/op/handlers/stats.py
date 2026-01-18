from __future__ import annotations

import math
from typing import Any

from aiogram import flags
from stfu_tg import Bold, Code, Doc, Italic, KeyValue, Section, Template

from sophie_bot.config import CONFIG
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.modules import LOADED_MODULES
from sophie_bot.modules.help.utils.extract_info import get_all_cmds_raw
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.services.db import db
from sophie_bot.services.redis import aredis
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.versions import SOPHIE_BRANCH, SOPHIE_COMMIT, SOPHIE_VERSION


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


async def get_system_stats() -> Doc:
    doc = Doc()

    doc += Section(
        Italic(CONFIG.environment),
        Bold("Debug mode enabled!") if CONFIG.debug_mode else None,
        KeyValue("Version", Italic(SOPHIE_VERSION)),
        KeyValue("Commit", Code(SOPHIE_COMMIT)),
        KeyValue("Branch", Italic(SOPHIE_BRANCH)),
        KeyValue("Webhooks", Code(CONFIG.webhooks_port)) if CONFIG.webhooks_enable else "Long-polling mode",
        title="Environment",
    )

    technical_section = Section(title="Technical info")

    local_db = await db.command("dbstats")
    if "fsTotalSize" in local_db:
        technical_section += KeyValue(
            "Database size",
            Template(
                "{db_size}, free {db_free}",
                db_size=Code(convert_size(local_db["dataSize"])),
                db_free=Code(convert_size(local_db["fsTotalSize"] - local_db["fsUsedSize"])),
            ),
        )
    else:
        technical_section += KeyValue(
            "Database size",
            Template(
                "{db_size}, free {db_free}",
                db_size=Code(convert_size(local_db["storageSize"])),
                db_free=Code(convert_size(536870912 - local_db["storageSize"])),
            ),
        )

    technical_section += KeyValue("Redis keys", Code(await aredis.dbsize()))

    technical_section += KeyValue("Modules", Template("{modules} loaded", modules=Code(len(LOADED_MODULES))))
    technical_section += KeyValue(
        "Legacy modules",
        Template(
            "{cmds} total commands registered, in {modules} modules",
            cmds=Code(len(get_all_cmds_raw())),
            modules=Code(len(LOADED_MODULES)),
        ),
    )

    doc += technical_section
    return doc


@flags.help(description=l_("Show bot statistics."))
class StatsHandler(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter(("stats",)), IsOP(True))

    async def handle(self):
        sec = Doc()

        all_modules: list[Any] = list(LOADED_MODULES.values())
        all_modules.extend(LOADED_MODULES)

        for module in all_modules:
            if hasattr(module, "__stats__"):
                res = module.__stats__()
                if hasattr(res, "__await__"):
                    res = await res
                sec += res

        await self.event.reply(str(sec))
