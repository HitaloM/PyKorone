# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

from typing import Union

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message


async def sudo_filter(_, client: Client, union: Union[CallbackQuery, Message]) -> bool:
    user = union.from_user
    if not user:
        return False
    return client.is_sudoer(user)


filters.sudoer = filters.create(sudo_filter, "FilterSudo")
