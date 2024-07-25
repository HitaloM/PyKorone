import math
import os

import ujson
from aiogram import Router
from aiogram.types import Message
from stfu_tg import Code, KeyValue, Section, Template

from sophie_bot import SOPHIE_VERSION
from sophie_bot.config import CONFIG
from sophie_bot.filters.user_status import IsOP
from sophie_bot.modules import LOADED_MODULES
from sophie_bot.modules.legacy_modules.modules import LOADED_LEGACY_MODULES
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.register import (
    REGISTRED_COMMANDS,
    register,
)
from sophie_bot.services.db import db
from sophie_bot.services.redis import redis

router = Router(name="owner_stuff")


__exclude_public__ = True


@register(router, IsOP(True), cmds="event")
async def get_event(message):
    print(message)
    event = str(ujson.dumps(message, indent=2))
    await message.reply(event)


@register(router, IsOP(True), cmds="stats")
async def stats(message):
    sec = Section(title=f"Sophie {SOPHIE_VERSION}")

    all_modules = [*LOADED_LEGACY_MODULES, *LOADED_MODULES.values()]

    for module in [m for m in all_modules if hasattr(m, "__stats__")]:
        sec += await module.__stats__()

    await message.reply(str(sec))


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


async def __stats__():
    sec = Section(title="Technical information")

    if os.getenv("WEBHOOKS", False):
        sec += f"Webhooks mode, listen port: <code>{os.getenv('WEBHOOKS_PORT', 8080)}</code>"
    else:
        sec += "Long-polling mode"
    local_db = await db.command("dbstats")
    if "fsTotalSize" in local_db:
        sec += Template(
            "Database size is {db_size}, free {db_free}",
            db_size=Code(convert_size(local_db["dataSize"])),
            db_free=Code(convert_size(local_db["fsTotalSize"] - local_db["fsUsedSize"])),
        )
    else:
        sec += Template(
            "Database size is {db_size}, free {db_free}",
            db_size=Code(convert_size(local_db["storageSize"])),
            db_free=Code(convert_size(536870912 - local_db["storageSize"])),
        )

    sec += Template("{redis_keys} total keys in Redis database", redis_keys=Code(len(redis.keys())))
    sec += KeyValue(
        "Legacy modules",
        Template(
            "{cmds} total commands registered, in {modules} modules",
            cmds=Code(len(REGISTRED_COMMANDS)),
            modules=Code(len(LOADED_LEGACY_MODULES)),
        ),
    )
    sec += KeyValue("Modules", Template("{modules} loaded", modules=Code(len(LOADED_MODULES))))
    return sec


@get_strings_dec("owner_stuff")
async def __user_info__(message: Message, user_id, strings):
    if user_id == CONFIG.owner_id:
        return strings["father"]
    elif user_id in CONFIG.operators:
        return strings["sudo_crown"]
