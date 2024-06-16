# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram

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

import html
import sys
import traceback

from aiogram.types import ErrorEvent
from redis.exceptions import RedisError

from sophie_bot import dp, bot
from sophie_bot.config import CONFIG
from sophie_bot.services.redis import redis
from sophie_bot.utils.logger import log

SENT = []


def catch_redis_error(**dec_kwargs):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            global SENT
            # We can't use redis here
            # So we save data - 'message sent to' in a list variable
            event: ErrorEvent = args[0]

            if event.update.message is not None:
                message = event.update.message
            elif event.update.callback_query is not None:
                message = event.update.callback_query
            elif event.update.edited_message is not None:
                message = event.update.edited_message
            else:
                return True

            chat_id = message.chat.id if 'chat' in message else None
            try:
                return await func(*args, **kwargs)
            except RedisError:
                if chat_id not in SENT:
                    text = 'Sorry for inconvenience! I encountered error in my redis DB, which is necessary for  ' \
                           'running bot \n\nPlease report this to my support group immediately when you see this error!'
                    if await bot.send_message(chat_id, text):
                        SENT.append(chat_id)
                # Alert bot owner
                if CONFIG.owner_id not in SENT:
                    text = 'Sophie panic: Got redis error'
                    if await bot.send_message(CONFIG.owner_id, text):
                        SENT.append(CONFIG.owner_id)
                log.error(RedisError, exc_info=True)
                return True

        return wrapped_1

    return wrapped


@dp.error()
# @catch_redis_error()
async def all_errors_handler(event: ErrorEvent):
    log.error(event.exception)
    log.error(traceback.format_exc())

    if event.update.message is not None:
        update = event.update.message
        chat_id = update.chat.id
    elif event.update.callback_query is not None:
        update = event.update.callback_query
        chat_id = update.from_user.id
    elif event.update.edited_message is not None:
        update = event.update.edited_message
        chat_id = update.chat.id
    else:
        return True

    err_tlt = sys.exc_info()[0].__name__
    err_msg = str(sys.exc_info()[1])

    if redis.get(chat_id) == str(event.exception):
        # by err_tlt we assume that it is same error
        return True

    if err_tlt == 'BadRequest' and err_msg == 'Have no rights to send a message':
        return True

    ignored_errors = (
        'FloodWaitError', 'RetryAfter', 'SlowModeWaitError', 'InvalidQueryID'
    )
    if err_tlt in ignored_errors:
        return True

    if err_tlt in ('NetworkError', 'TelegramAPIError', 'RestartingTelegram'):
        log.error("Conn/API error detected", exc_info=event.exception)
        return True

    text = "<b>Sorry, I encountered a error!</b>\n"
    text += f'<code>{html.escape(err_tlt, quote=False)}</code>'
    redis.set(chat_id, str(event.exception), ex=600)
    await bot.send_message(chat_id, text)
