# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
import math
import os

import ujson

from sophie_bot.config import CONFIG
from sophie_bot.legacy_modules import LOADED_MODULES
from sophie_bot.services.db import db
from sophie_bot.services.redis import redis
from sophie_bot.utils.i18n import gettext as _
from .utils.language import get_strings_dec
from .utils.register import register, REGISTRED_COMMANDS
from sophie_bot.filters.user_status import IsOP


#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


@register(IsOP(True), cmds="crash")
async def crash(message):
    test = 2 / 0
    print(test)


@register(IsOP(True), cmds="event")
async def get_event(message):
    print(message)
    event = str(ujson.dumps(message, indent=2))
    await message.reply(event)


@register(IsOP(True), cmds="stats")
async def stats(message):
    text = _("<b>Sophie stats</b>\n")

    for module in [m for m in LOADED_MODULES if hasattr(m, '__stats__')]:
        text += await module.__stats__()

    await message.reply(text)


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


async def __stats__():
    text = ""
    if os.getenv('WEBHOOKS', False):
        text += f"* Webhooks mode, listen port: <code>{os.getenv('WEBHOOKS_PORT', 8080)}</code>\n"
    else:
        text += "* Long-polling mode\n"
    local_db = await db.command("dbstats")
    if 'fsTotalSize' in local_db:
        text += '* Database size is <code>{}</code>, free <code>{}</code>\n'.format(
            convert_size(local_db['dataSize']),
            convert_size(local_db['fsTotalSize'] - local_db['fsUsedSize'])
        )
    else:
        text += '* Database size is <code>{}</code>, free <code>{}</code>\n'.format(
            convert_size(local_db['storageSize']),
            convert_size(536870912 - local_db['storageSize'])
        )

    text += "* <code>{}</code> total keys in Redis database\n".format(len(redis.keys()))
    text += "* <code>{}</code> total commands registred, in <code>{}</code> modules\n".format(
        len(REGISTRED_COMMANDS), len(LOADED_MODULES))
    return text


@get_strings_dec('owner_stuff')
async def __user_info__(message, user_id, strings):
    if user_id == CONFIG.owner_id:
        return strings["father"]
    elif user_id in CONFIG.operators:
        return strings['sudo_crown']
