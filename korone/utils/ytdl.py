# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import asyncio
import time

from pyrogram.errors import BadRequest, FloodWait

from korone.utils import aiowrap


@aiowrap
def extract_info(instance, url, download=True):
    return instance.extract_info(url, download)
