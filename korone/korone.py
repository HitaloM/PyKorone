# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import logging
import platform
from datetime import datetime, timezone

import pyrogram
import sentry_sdk
from pyrogram import Client
from pyrogram.errors import BadRequest, ChatWriteForbidden
from pyrogram.helpers import ikb
from pyrogram.raw.all import layer
from pyrogram.types import Message, User

import korone
from korone.config import API_HASH, API_ID, LOGS_CHANNEL, SENTRY_KEY, SUDOERS, TOKEN
from korone.utils import shell_exec
from korone.utils.langs import get_languages, load_languages

log = logging.getLogger(__name__)


class Korone(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()
        self.is_sudo = SUDOERS

        super().__init__(
            name=name,
            app_version=f"PyKorone v{korone.__version__}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=TOKEN,
            parse_mode="html",
            workers=24,
            workdir="korone",
            plugins={"root": "korone.modules"},
            sleep_threshold=180,
        )

        # Save start time (useful for uptime info)
        self.start_time = datetime.now().replace(tzinfo=timezone.utc)

    async def start(self):
        # Start Pyrogram client
        await super().start()

        # Load the languages
        load_languages()
        languages = len(get_languages(only_codes=True))
        log.info("%s languages was loaded.", languages)

        # Saving commit number
        self.version_code = int((await shell_exec("git rev-list --count HEAD"))[0])

        # Some useful vars
        self.me = await self.get_me()
        self.ikb = ikb

        if not SENTRY_KEY or SENTRY_KEY == "":
            log.warning("No sentry.io key found! Service not initialized.")
        else:
            log.info("Starting sentry.io service.")
            sentry_sdk.init(SENTRY_KEY, traces_sample_rate=1.0)

        log.info(
            "PyKorone for Pyrogram v%s (Layer %s) started on @%s. Hi.",
            pyrogram.__version__,
            layer,
            self.me.username,
        )

        # Startup message
        start_message = (
            f"<b>PyKorone <code>v{self.version_code}</code> started...</b>\n"
            f"- <b>Pyrogram:</b> <code>v{pyrogram.__version__}</code>\n"
            f"- <b>Python:</b> <code>v{platform.python_version()}</code>\n"
            f"- <b>Languages:</b> <code>{languages}</code>\n"
            f"- <b>System:</b> <code>{self.system_version}</code>"
        )
        try:
            await self.send_message(chat_id=LOGS_CHANNEL, text=start_message)
        except (BadRequest, ChatWriteForbidden):
            log.warning("Unable to send the startup message to the LOGS_CHANNEL!")

    async def restart(self, *args):
        log.info("PyKorone client is restarting...")
        await super().restart(*args)

    async def stop(self, *args):
        await super().stop(*args)
        log.info("PyKorone stopped... Bye.")

    async def int_reply(self, m: Message, text: str, *args, **kwargs):
        if m.chat.type == "private":
            await m.reply_text(text, *args, **kwargs)
        elif m.reply_to_message and (
            m.reply_to_message.from_user is not None
            and m.reply_to_message.from_user.id == self.me.id
        ):
            await m.reply_text(text, *args, **kwargs)
        return

    async def send_log(self, text: str, *args, **kwargs):
        await self.send_message(
            chat_id=LOGS_CHANNEL,
            text=text,
            *args,
            **kwargs,
        )
        return

    def is_sudoer(self, user: User) -> bool:
        return user.id in self.is_sudo
