# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
import typing
from datetime import timedelta

from aiogram.types import Message

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# elif raw_button[1] == 'note':
# t = InlineKeyboardButton(raw_button[0], callback_data='get_note_{}_{}'.format(chat_id, raw_button[2]))
# elif raw_button[1] == 'alert':
# t = InlineKeyboardButton(raw_button[0], callback_data='get_alert_{}_{}'.format(chat_id, raw_button[2]))
# elif raw_button[1] == 'deletemsg':
# t = InlineKeyboardButton(raw_button[0], callback_data='get_delete_msg_{}_{}'.format(chat_id, raw_button[2]))


class InvalidTimeUnit(Exception):
    pass


def get_arg(message):
    try:
        return get_args_str(message).split()[0]
    except IndexError:
        return ""


def get_full_command(message: Message) -> typing.Optional[tuple[str, str]]:
    text = message.text or message.caption
    command, *args = text.split(maxsplit=1)
    args = args[0] if args else ""
    return command, args


def get_args(message: Message):
    args = get_full_command(message)[1].split()
    if args is None:
        # getting args from non-command
        args = message.text.split()
    return args


def get_args_str(message):
    return " ".join(get_args(message))


def get_cmd(message: Message):
    cmd = get_full_command(message)[0].lower()[1:].split("@")[0]
    return cmd


def convert_time(time_val):
    if not any(time_val.endswith(unit) for unit in ("m", "h", "d")):
        raise TypeError

    time_num = int(time_val[:-1])
    unit = time_val[-1]
    kwargs = {}

    if unit == "m":
        kwargs["minutes"] = time_num
    elif unit == "h":
        kwargs["hours"] = time_num
    elif unit == "d":
        kwargs["days"] = time_num
    else:
        raise InvalidTimeUnit()

    val = timedelta(**kwargs)

    return val


def need_args_dec(num=1):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            message = args[0]
            if len(message.text.split(" ")) > num:
                return await func(*args, **kwargs)
            else:
                await message.reply("No enoff args!")

        return wrapped_1

    return wrapped
