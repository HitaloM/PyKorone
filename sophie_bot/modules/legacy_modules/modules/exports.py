import asyncio
from datetime import datetime, timedelta

import ujson
from aiogram import Router
from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile
from babel.dates import format_timedelta

from sophie_bot import CONFIG
from sophie_bot.modules.legacy_modules import LOADED_LEGACY_MODULES
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.register import register
from sophie_bot.services.redis import redis

VERSION = 5

router = Router(name="exports")


@register(router, cmds="export", user_admin=True)
@get_strings_dec("imports_exports")
async def export_chat_data(message: Message, strings):
    chat_id = message.chat.id
    key = "export_lock:" + str(chat_id)
    if redis.get(key) and message.from_user.id not in CONFIG.operators:
        ttl = format_timedelta(timedelta(seconds=redis.ttl(key)), strings["language_info"]["babel"])
        await message.reply(strings["exports_locked"] % ttl)
        return

    redis.set(key, 1)
    redis.expire(key, 7200)

    msg = await message.reply(strings["started_exporting"])
    data = {
        "general": {
            "chat_name": "Private",
            "chat_id": chat_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": VERSION,
        }
    }

    for module in [m for m in LOADED_LEGACY_MODULES if hasattr(m, "__export__")]:
        await asyncio.sleep(0)  # Switch to other events before continue
        if k := await module.__export__(chat_id):
            data.update(k)

    jfile = BufferedInputFile(str(ujson.dumps(data, indent=2)).encode(), filename="fban_info.txt")
    text = strings["export_done"].format(chat_name="Private")
    await message.answer_document(jfile, caption=text, reply=message.message_id)
    await msg.delete()
