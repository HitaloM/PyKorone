# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import datetime

from pyrogram import Client
from pyrogram.types import InputMediaDocument

from korone.config import config

from .logger import log


async def save(bot: Client):
    date = datetime.datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

    log.warning(
        "[%s] Saving the database in Telegram...",
        bot.name,
    )

    try:
        if await bot.send_media_group(
            config.get_config("backups_channel"),
            [
                InputMediaDocument(media="./korone/korone.session"),
                InputMediaDocument(
                    media="./korone/database/db.sqlite",
                    caption=f"<b>BACKUP</b>\n\n<b>Date</b>: <code>{date}</code>",
                ),
            ],
        ):
            log.warning(
                "[%s] Backup saved in Telegram successfully!",
                bot.name,
            )
        else:
            log.warning(
                "[%s] It was not possible to save the backup in Telegram.",
                bot.name,
            )
    except BaseException:
        log.error("Error saving the backup in Telegram.", exc_info=True)
